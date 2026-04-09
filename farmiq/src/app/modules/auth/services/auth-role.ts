/**
 * AUTHENTICATION & ROLE SERVICE - ENHANCED WITH ANGULAR SIGNALS
 * 
 * Comprehensive service for managing user authentication and role-based access
 * Uses Angular Signals for reactive state management
 * Handles cross-service communication for role changes
 * 
 * Features:
 * - Signals-based state (userProfile, userRoles, currentRole)
 * - Role caching to prevent duplicate edge function calls
 * - Cross-service communication via RxJS Subject
 * - Automatic profile refresh on role changes
 * - FarmIQ ID integration
 */

import { Injectable, signal, computed, inject, effect, PLATFORM_ID } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import { Observable, BehaviorSubject, Subject } from 'rxjs';
import { switchMap, tap, map } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';

// Core services (now located in core services)
import { SupabaseService, FarmiqIdService } from '../../../services/core';
import { RoleService } from './role';

import {
  UserProfile,
  UserProfileUpdateRequest,
  UserRoleType,
  SignupData,
  UserRole as UserRoleModel,
} from '../models';

import { KENYAN_COUNTIES, KENYAN_CROPS, COOPERATIVE_TYPES, FARMING_METHODS, LENDER_TYPES } from '../models/auth.models';

export type UserRole = UserRoleType;

/**
 * Role change event for cross-service communication
 */
export interface RoleChangeEvent {
  userId: string;
  role: UserRole;
  action: 'assign' | 'revoke' | 'update';
  timestamp: Date;
}

@Injectable({
  providedIn: 'root',
})
export class AuthRoleService {
  private apiUrl = '/api/auth';
  
  // Inject dependencies
  private supabase = inject(SupabaseService);
  private roleService = inject(RoleService);
  private http = inject(HttpClient);
  private router = inject(Router);
  private farmiqIdService = inject(FarmiqIdService);
  protected platformId = inject(PLATFORM_ID);
  
  // ============================================================================
  // ANGULAR SIGNALS - PRIMARY STATE MANAGEMENT
  // ============================================================================
  
  private userProfileSignal = signal<UserProfile | null>(null);
  private userRolesSignal = signal<UserRole[]>([]);
  private currentRoleSignal = signal<UserRole | null>(null);
  private isLoadingSignal = signal<boolean>(false);
  private errorSignal = signal<string | null>(null);
  private lastProfileRefreshSignal = signal<Date | null>(null);
  private rolesCacheSignal = signal<Map<string, UserRole[]>>(new Map());
  private isOAuthSetupSignal = signal<boolean>(false);
  
  // ✅ FIX: Cache management with TTL tracking
  private roleCacheTimestampsSignal = signal<Map<string, number>>(new Map());
  private readonly ROLE_CACHE_TTL_MS = 30 * 1000; // 30 seconds
  private cacheCleanupInterval: any = null;
  
  // Public read-only signals for components
  public userProfile$ = this.userProfileSignal.asReadonly();
  public userRoles$ = this.userRolesSignal.asReadonly();
  public currentRole$ = this.currentRoleSignal.asReadonly();
  public isLoading$ = this.isLoadingSignal.asReadonly();
  public error$ = this.errorSignal.asReadonly();
  
  // Computed signals
  public hasUserProfile = computed(() => this.userProfileSignal() !== null);
  public isAuthenticated = computed(() => this.hasUserProfile() && this.currentRoleSignal() !== null);
  public primaryRoleLabel = computed(() => {
    const role = this.currentRoleSignal();
    return role ? this.getRoleLabel(role) : 'No Role';
  });
  public allRoleLabels = computed(() => {
    return this.userRolesSignal().map(role => this.getRoleLabel(role));
  });
  
  // ============================================================================
  // CROSS-SERVICE COMMUNICATION
  // ============================================================================
  
  private roleChangeSubject = new Subject<RoleChangeEvent>();
  public roleChange$ = this.roleChangeSubject.asObservable();
  
  // ============================================================================
  // BACKWARD COMPATIBILITY - RXJS OBSERVABLES
  // ============================================================================
  
  private userProfileSubject = new BehaviorSubject<UserProfile | null>(null);
  private userRoleSubject = new BehaviorSubject<UserRole | null>(null);
  
  // Legacy observables for backward compatibility
  userRole$ = this.userRoleSubject.asObservable();

  // Role-to-dashboard mapping
  private roleDashboardMap: Record<UserRole, string> = {
    farmer: '/farmer/setup',
    cooperative: '/cooperative',
    lender: '/lender',
    agent: '/agent',
    vendor: '/vendor',
    worker: '/worker',
    admin: '/admin',
  };

  // Kenya counties and crops for validation
  get kenyanCounties(): string[] {
    return KENYAN_COUNTIES;
  }

  get kenyaCrops(): string[] {
    return KENYAN_CROPS;
  }

  constructor() {
    this.initializeService();
  }

  /**
   * Initialize service and set up effects
   */
  private initializeService(): void {
    // ✅ FIX: Start cache cleanup interval (runs every 2 minutes)
    this.startCacheCleanupInterval();

    // Watch authentication state and load profile when authenticated
    // BUT skip during OAuth setup to avoid calling edge functions before profile exists
    effect(() => {
      const isAuth = this.supabase.isAuthenticatedSignal$();
      const isOAuthSetup = this.isOAuthSetupSignal();
      
      if (isAuth && !isOAuthSetup) {
        console.log('✅ User authenticated, loading profile...');
        this.loadUserProfile().subscribe();
      } else if (!isAuth) {
        // Only log in browser to avoid excessive SSR logs during prerendering
        if (this.platformId && isPlatformBrowser(this.platformId)) {
          console.log('❌ User not authenticated, clearing profile...');
        }
        this.clearProfile();
      } else if (isOAuthSetup) {
        console.log('⏳ OAuth setup in progress, deferring profile load until role selection completes');
      }
    });

    // Watch for role changes from RoleService and refresh profile
    this.roleService.roleChange$.subscribe((event: RoleChangeEvent) => {
      const currentProfile = this.userProfileSignal();
      if (currentProfile && event.userId === currentProfile.id) {
        console.log(`Role ${event.action} detected for user, refreshing profile...`);
        // ✅ FIX: Invalidate cache when role changes to ensure fresh data
        this.invalidateRoleCache();
        this.loadUserProfile().subscribe();
      }
    });

    // Sync signals to legacy subjects for backward compatibility
    effect(() => {
      const profile = this.userProfileSignal();
      this.userProfileSubject.next(profile);
    });

    effect(() => {
      const role = this.currentRoleSignal();
      this.userRoleSubject.next(role);
    });
  }

  /**
   * Load user profile and roles from Supabase
   * Calls get-primary-role edge function to determine user's primary role
   * Fetches FarmIQ ID from user_profiles table
   * Caches roles to prevent duplicate calls
   */
  loadUserProfile(): Observable<UserProfile> {
    return new Observable(observer => {
      const user = this.supabase.getUser();
      if (!user) {
        this.errorSignal.set('User not authenticated');
        observer.error(new Error('User not authenticated'));
        return;
      }

      this.isLoadingSignal.set(true);
      this.errorSignal.set(null);

      // Get user profile directly from database instead of edge function
      this.supabase.getSupabaseClient().then(client => {
        client
          .from('user_profiles')
          .select('*')
          .eq('id', user.id)
          .single()
          .then(({ data: profile, error }) => {
            if (error) {
              // For OAuth users during initial setup, the profile might not exist yet
              const statusCode = error?.code;
              if (statusCode === 'PGRST116' || statusCode === 'PGRST204') {
                console.warn('⚠️ Profile not ready yet (404/204), returning basic profile for OAuth setup:', error.message);
                
                // Create a minimal profile for now
                const basicProfile: UserProfile = {
                  id: user.id,
                  farmiq_id: '',
                  email: user.email || '',
                  first_name: user.user_metadata?.['first_name'] || user.user_metadata?.['firstName'] || '',
                  last_name: user.user_metadata?.['last_name'] || user.user_metadata?.['lastName'] || '',
                  primary_role: 'farmer',
                  phone_number: '',
                  email_verified: user.email_confirmed_at !== null && user.email_confirmed_at !== undefined,
                  profile_completed: false,
                  created_at: user.created_at ? new Date(user.created_at).toISOString() : new Date().toISOString(),
                  updated_at: new Date().toISOString(),
                };
                
                this.userProfileSignal.set(basicProfile);
                this.isLoadingSignal.set(false);
                observer.next(basicProfile);
                observer.complete();
                return;
              }
              
              // For other errors, log and return error
              console.error('Error loading profile:', error);
              this.errorSignal.set(error.message || 'Failed to load user profile');
              this.isLoadingSignal.set(false);
              observer.error(error);
              return;
            }

            if (!profile) {
              console.warn('⚠️ No profile found for user, creating basic profile');
              const basicProfile: UserProfile = {
                id: user.id,
                farmiq_id: '',
                email: user.email || '',
                first_name: user.user_metadata?.['first_name'] || user.user_metadata?.['firstName'] || '',
                last_name: user.user_metadata?.['last_name'] || user.user_metadata?.['lastName'] || '',
                primary_role: 'farmer',
                phone_number: '',
                email_verified: user.email_confirmed_at !== null && user.email_confirmed_at !== undefined,
                profile_completed: false,
                created_at: user.created_at ? new Date(user.created_at).toISOString() : new Date().toISOString(),
                updated_at: new Date().toISOString(),
              };
              
              this.userProfileSignal.set(basicProfile);
              this.isLoadingSignal.set(false);
              observer.next(basicProfile);
              observer.complete();
              return;
            }

            const userProfile: UserProfile = {
              id: user.id,
              farmiq_id: profile.farmiq_id || '',
              email: user.email || '',
              first_name: user.user_metadata?.['first_name'] || user.user_metadata?.['firstName'] || '',
              last_name: user.user_metadata?.['last_name'] || user.user_metadata?.['lastName'] || '',
              primary_role: (profile.primary_role as UserRole) || 'farmer',
              phone_number: user.user_metadata?.['phone_number'] || user.user_metadata?.['phoneNumber'] || '',
              email_verified: user.email_confirmed_at !== null && user.email_confirmed_at !== undefined,
              profile_completed: profile.profile_completed || false,
              created_at: user.created_at ? new Date(user.created_at).toISOString() : new Date().toISOString(),
              updated_at: new Date().toISOString(),
            };

            // Update signals
            this.userProfileSignal.set(userProfile);
            this.currentRoleSignal.set(userProfile.primary_role as UserRoleType);
            this.lastProfileRefreshSignal.set(new Date());

            // Store FarmIQ ID in localStorage
            if (userProfile.farmiq_id) {
              this.farmiqIdService.setFarmiqId(userProfile.farmiq_id);
            }

            // Load all user roles (with caching)
            this.loadUserRoles(user.id).subscribe({
              next: (roles) => {
                this.userRolesSignal.set(roles);
                this.isLoadingSignal.set(false);
                observer.next(userProfile);
                observer.complete();
              },
              error: (error) => {
                console.warn('Could not load all roles, continuing with primary role:', error);
                this.isLoadingSignal.set(false);
                observer.next(userProfile);
                observer.complete();
              }
            });
          });
      }).catch((error) => {
        console.error('Error getting Supabase client:', error);
        this.errorSignal.set('Failed to initialize database client');
        this.isLoadingSignal.set(false);
        observer.error(error);
      });
    });
  }

  /**
   * Load all roles assigned to user with TTL-based caching
   * Prevents duplicate database queries within cache TTL (30 seconds)
   * Uses direct database access instead of edge functions
   */
  private loadUserRoles(userId: string): Observable<UserRole[]> {
    return new Observable(observer => {
      const cache = this.rolesCacheSignal();
      const timestamps = this.roleCacheTimestampsSignal();
      const cachedRoles = cache.get(userId);
      const cacheTimestamp = timestamps.get(userId);
      
      // Check cache validity with TTL
      const now = Date.now();
      const cacheExpired = !cacheTimestamp || (now - cacheTimestamp) > this.ROLE_CACHE_TTL_MS;
      
      if (cachedRoles && !cacheExpired) {
        console.log(`📦 Using cached roles for user (${Math.round((this.ROLE_CACHE_TTL_MS - (now - cacheTimestamp)) / 1000)}s remaining)`);
        observer.next(cachedRoles);
        observer.complete();
        return;
      }

      console.log('🔄 Cache expired or not found, fetching roles from database...');

      // Query database directly instead of edge function
      this.supabase.getSupabaseClient().then(client => {
        client
          .from('user_roles')
          .select('id, role, is_active, assigned_at')
          .eq('user_id', userId)
          .eq('is_active', true)
          .then(({ data: rolesData, error }) => {
            if (error) {
              console.warn('Error loading user roles:', error);
              observer.error(error);
              return;
            }

            const roles = (rolesData || []).map(r => r.role as UserRole);
            
            // Update cache with timestamp
            const updatedCache = new Map(cache);
            const updatedTimestamps = new Map(timestamps);
            updatedCache.set(userId, roles);
            updatedTimestamps.set(userId, Date.now());
            
            this.rolesCacheSignal.set(updatedCache);
            this.roleCacheTimestampsSignal.set(updatedTimestamps);

            console.log(`✅ Roles cached for ${this.ROLE_CACHE_TTL_MS / 1000}s:`, roles);
            observer.next(roles);
            observer.complete();
          });
      }).catch((error) => {
        console.error('Error getting Supabase client:', error);
        observer.error(error);
      });
    });
  }

  /**
   * Refresh user roles (invalidates cache)
   * Called when roles change or explicit refresh needed
   */
  public refreshUserRoles(): Observable<UserRole[]> {
    const profile = this.userProfileSignal();
    if (!profile) {
      return new Observable(observer => {
        observer.error(new Error('No user profile loaded'));
      });
    }

    // ✅ FIX: Clear both cache and timestamp
    this.invalidateRoleCache(profile.id);

    // Reload roles
    return this.loadUserRoles(profile.id).pipe(
      tap(roles => {
        this.userRolesSignal.set(roles);
        console.log('✅ User roles refreshed:', roles);
      })
    );
  }

  /**
   * ✅ FIX: Invalidate role cache for specific user or all users
   * Called when role changes detected or explicit refresh needed
   */
  private invalidateRoleCache(userId?: string): void {
    const cache = this.rolesCacheSignal();
    const timestamps = this.roleCacheTimestampsSignal();
    
    if (userId) {
      cache.delete(userId);
      timestamps.delete(userId);
      console.log(`🗑️  Cache invalidated for user ${userId.substring(0, 8)}...`);
    } else {
      this.rolesCacheSignal.set(new Map());
      this.roleCacheTimestampsSignal.set(new Map());
      console.log('🗑️  All role caches invalidated');
    }
    
    this.rolesCacheSignal.set(cache);
    this.roleCacheTimestampsSignal.set(timestamps);
  }

  /**
   * ✅ FIX: Start cache cleanup interval to remove expired entries
   * Runs every 2 minutes to clean up stale cache entries
   */
  private startCacheCleanupInterval(): void {
    if (this.cacheCleanupInterval) {
      clearInterval(this.cacheCleanupInterval);
    }

    this.cacheCleanupInterval = setInterval(() => {
      const cache = this.rolesCacheSignal();
      const timestamps = this.roleCacheTimestampsSignal();
      const now = Date.now();
      let cleanedCount = 0;

      for (const [userId, timestamp] of timestamps.entries()) {
        if ((now - timestamp) > this.ROLE_CACHE_TTL_MS) {
          cache.delete(userId);
          timestamps.delete(userId);
          cleanedCount++;
        }
      }

      if (cleanedCount > 0) {
        this.rolesCacheSignal.set(cache);
        this.roleCacheTimestampsSignal.set(timestamps);
        console.log(`🧹 Cache cleanup: Removed ${cleanedCount} expired entries`);
      }
    }, 2 * 60 * 1000); // Run every 2 minutes
  }

  /**
   * Set OAuth setup flag to defer profile loading during role selection
   * Call this when entering OAuth flow, call with false when complete
   */
  public setOAuthSetup(isSetup: boolean): void {
    console.log(isSetup ? '🔐 OAuth setup started, deferring profile load' : '✅ OAuth setup complete, resuming profile load');
    this.isOAuthSetupSignal.set(isSetup);
    
    // If OAuth setup is complete, trigger profile load now
    if (!isSetup && this.supabase.isAuthenticatedSignal$()) {
      console.log('🔄 OAuth setup complete, loading profile now...');
      setTimeout(() => {
        this.loadUserProfile().subscribe();
      }, 500);
    }
  }

  /**
   * Check if user has specific role
   */
  hasRole(role: UserRole): boolean {
    const roles = this.userRolesSignal();
    return roles.includes(role);
  }

  /**
   * Check if user has any of the specified roles
   */
  hasAnyRole(roles: UserRole[]): boolean {
    const userRoles = this.userRolesSignal();
    return roles.some(role => userRoles.includes(role));
  }

  /**
   * Check access for specific module with role
   */
  async checkRoleAccess(roleType: UserRole, module?: string): Promise<boolean> {
    const profile = this.userProfileSignal();
    if (!profile) return false;

    return this.roleService.checkRoleAccess(profile.id, roleType, module);
  }

  /**
   * Register user with role-specific data
   * Uses direct database calls instead of edge function to avoid OAuth token issues
   */
  registerUser(signupData: SignupData): Observable<any> {
    return new Observable(observer => {
      const user = this.supabase.getUser();
      if (!user) {
        observer.error(new Error('User not authenticated'));
        return;
      }

      // Use direct SupabaseService methods instead of edge function
      this.supabase.getSupabaseClient().then(async (client) => {
        try {
          // Step 1: Assign role to user
          await this.supabase.assignRoleToUser(user.id, signupData.selected_role as any);
          
          // Step 2: Update user's primary role
          await this.supabase.updateUserPrimaryRole(user.id, signupData.selected_role);
          
          // Step 3: Reload profile with new role
          this.loadUserProfile().subscribe({
            next: (profile) => {
              observer.next(profile);
              observer.complete();
            },
            error: (error) => observer.error(error)
          });
        } catch (error) {
          console.error('Error registering user:', error);
          observer.error(error);
        }
      }).catch((error) => {
        observer.error(error);
      });
    });
  }

  /**
   * Assign role to user (admin only)
   */
  async assignRole(userId: string, roleType: UserRole): Promise<boolean> {
    const result = await this.roleService.assignRole({ 
      userId: userId, 
      role: roleType 
    });

    if (result.success) {
      // Notify other services
      this.roleChangeSubject.next({
        userId,
        role: roleType,
        action: 'assign',
        timestamp: new Date()
      });

      // Refresh current user profile if it's the same user
      const profile = this.userProfileSignal();
      if (profile && profile.id === userId) {
        await this.refreshUserRoles().toPromise();
      }
    }

    return result.success;
  }

  /**
   * Revoke role from user (admin only)
   */
  async revokeRole(userId: string, roleId: string): Promise<boolean> {
    const success = await this.roleService.revokeRole(userId, roleId);

    if (success) {
      // Notify other services
      const roles = this.userRolesSignal();
      const revokedRole = roles[0] as UserRole; // Simplified - should track which role was revoked
      
      this.roleChangeSubject.next({
        userId,
        role: revokedRole,
        action: 'revoke',
        timestamp: new Date()
      });

      // Refresh current user profile if it's the same user
      const profile = this.userProfileSignal();
      if (profile && profile.id === userId) {
        await this.refreshUserRoles().toPromise();
      }
    }

    return success;
  }

  /**
   * Update user profile
   * Uses direct database calls instead of edge function
   */
  updateUserProfile(profileData: UserProfileUpdateRequest): Observable<UserProfile> {
    return new Observable(observer => {
      const user = this.supabase.getUser();
      if (!user) {
        observer.error(new Error('User not authenticated'));
        return;
      }

      // Update user profile directly in database
      this.supabase.getSupabaseClient().then(async (client) => {
        try {
          const { error } = await client
            .from('user_profiles')
            .update({
              ...profileData,
              updated_at: new Date().toISOString()
            })
            .eq('id', user.id);

          if (error) {
            throw error;
          }

          // Update local profile signal
          const currentProfile = this.userProfileSignal();
          if (currentProfile) {
            const updatedProfile: UserProfile = {
              ...currentProfile,
              ...profileData,
              updated_at: new Date().toISOString()
            };
            this.userProfileSignal.set(updatedProfile);
            observer.next(updatedProfile);
          } else {
            observer.error(new Error('No profile loaded'));
          }
          observer.complete();
        } catch (error) {
          console.error('Error updating user profile:', error);
          observer.error(error);
        }
      }).catch((error) => {
        observer.error(error);
      });
    });
  }

  /**
   * Call Supabase edge function with proper authentication
   */
  private callEdgeFunction<T>(functionName: string, data: any): Observable<T> {
    return new Observable(observer => {
      (async () => {
        try {
          // Ensure session is valid and token is fresh
          const validSession = await this.supabase.ensureValidSession();
          
          if (!validSession?.access_token) {
            throw new Error('No valid auth token available. Please log in again.');
          }

          const supabaseUrl = environment.supabase?.url || 'https://tioauyhyrbqjbrypakex.supabase.co';
          
          console.log(`📞 Calling edge function: ${functionName} with valid token`);
          
          this.http.post<T>(
            `${supabaseUrl}/functions/v1/${functionName}`,
            data,
            {
              headers: {
                'Authorization': `Bearer ${validSession.access_token}`,
                'Content-Type': 'application/json'
              }
            }
          ).subscribe({
            next: (response) => observer.next(response),
            error: (error) => observer.error(error),
            complete: () => observer.complete()
          });
        } catch (error) {
          console.error(`❌ Error preparing edge function call (${functionName}):`, error);
          observer.error(error);
        }
      })();
    });
  }

  /**
   * Get redirect URL based on user role
   */
  getRoleRedirectUrl(role: UserRole): string {
    return this.roleDashboardMap[role] || '/login';
  }

  /**
   * Navigate to role-specific dashboard
   */
  navigateToRoleDashboard(role?: UserRole): void {
    const targetRole = role || this.currentRoleSignal();
    if (targetRole) {
      this.router.navigateByUrl(this.getRoleRedirectUrl(targetRole));
    } else {
      // No role assigned, redirect to login instead of non-existent dashboard
      console.warn('⚠️ No role assigned, redirecting to login');
      this.router.navigateByUrl('/login');
    }
  }

  /**
   * Get current user profile
   */
  getCurrentProfile(): UserProfile | null {
    return this.userProfileSignal();
  }

  /**
   * Get current user role
   */
  getCurrentRole(): UserRole | null {
    return this.currentRoleSignal();
  }

  /**
   * Get all user roles
   */
  getAllRoles(): UserRole[] {
    return this.userRolesSignal();
  }

  /**
   * Get role label for display
   */
  private getRoleLabel(role: UserRole): string {
    const labels: Record<UserRole, string> = {
      farmer: 'Farmer',
      cooperative: 'Cooperative',
      lender: 'Lender',
      agent: 'Agent',
      vendor: 'Vendor',
      worker: 'Worker',
      admin: 'Administrator'
    };
    return labels[role] || role;
  }

  /**
   * Clear all profile data (on logout)
   */
  private clearProfile(): void {
    this.userProfileSignal.set(null);
    this.userRolesSignal.set([]);
    this.currentRoleSignal.set(null);
    this.errorSignal.set(null);
    
    // ✅ FIX: Clear role caches on logout
    this.rolesCacheSignal.set(new Map());
    this.roleCacheTimestampsSignal.set(new Map());
    
    // ✅ FIX: Stop cache cleanup interval to prevent memory leaks and avoid accessing cleared caches
    if (this.cacheCleanupInterval) {
      clearInterval(this.cacheCleanupInterval);
      this.cacheCleanupInterval = null;
      console.log('🧹 Cache cleanup interval stopped on logout');
    }
    
    // Clear FarmIQ ID
    this.farmiqIdService.clearFarmiqId();
  }

  /**
   * Validate Kenya-specific requirements based on role
   */
  validateRoleSpecificData(signupData: SignupData): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Skip validation if no role-specific data is provided (user can complete profile after signup)
    switch (signupData.selected_role) {
      case 'farmer':
        // Only validate if at least one farmer field is provided
        if (signupData.farmer_data && (signupData.farmer_data.farm_name || signupData.farmer_data.location)) {
          if (!signupData.farmer_data.farm_name) errors.push('Farm name is required');
          if (!signupData.farmer_data.location) errors.push('Location is required');
        }
        break;

      case 'cooperative':
        // Only validate if at least one cooperative field is provided
        if (signupData.cooperative_data && (signupData.cooperative_data.cooperative_name || signupData.cooperative_data.registrationNumber)) {
          if (!signupData.cooperative_data.cooperative_name) errors.push('Cooperative name is required');
          if (!signupData.cooperative_data.registrationNumber) errors.push('Registration number is required');
        }
        break;

      case 'lender':
        // Only validate if at least one lender field is provided
        if (signupData.lender_data && (signupData.lender_data.institution_name || signupData.lender_data.institution_type)) {
          if (!signupData.lender_data.institution_name) errors.push('Institution name is required');
          if (!signupData.lender_data.institution_type) errors.push('Institution type is required');
        }
        break;
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }
}
