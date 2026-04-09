import { Injectable, signal, computed, effect, PLATFORM_ID, inject } from '@angular/core';
import { createClient, SupabaseClient, Session } from '@supabase/supabase-js';
import { isPlatformBrowser } from '@angular/common';
import { environment } from '../../../environments/environment';
import { AuthUser, SignUpRequest, SignInRequest, AuthResponse, UpdateProfileRequest } from '../../modules/auth/models/login.models';
import { ErrorHandlingService, ErrorType } from './error-handling.service';

@Injectable({
  providedIn: 'root',
})
export class SupabaseService {
  private supabase: SupabaseClient | null = null;
  private platformId = inject(PLATFORM_ID);
  private errorHandlingService = inject(ErrorHandlingService);
  
  // FarmIQ ID generation constants
  private readonly FARMIQ_PREFIX = 'FQ';
  private readonly FARMIQ_ID_LENGTH = 4;
  private readonly FARMIQ_CHARSET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  
  // Angular 21 Signals for reactive state (single source of truth)
  private sessionSignal = signal<Session | null>(null);
  private userSignal = signal<AuthUser | null>(null);
  private isAuthenticatedSignal = signal<boolean>(false);
  private isLoadingSignal = signal<boolean>(false);
  private tokenRefreshInProgressSignal = signal<boolean>(false);
  private isEmailVerifiedSignal = signal<boolean>(false);
  private emailVerificationRequiredSignal = signal<boolean>(false);
  private isOAuthSetupSignal = signal<boolean>(false);
  
  // ✅ FIX: Add OAuth provider detection signal (set BEFORE session retrieval)
  private oauthProviderDetectionSignal = signal<boolean>(false);
  
  // ✅ NEW: FarmIQ ID signal - stored after login/signup
  private farmiqIdSignal = signal<string | null>(null);
  
  // ✅ FIX: Email verification cache with TTL
  private emailVerificationCache = new Map<string, { verified: boolean; expiresAt: number }>();
  private readonly EMAIL_VERIFICATION_CACHE_TTL_MS = 30 * 60 * 1000; // 30 minutes

  // Public computed signals (read-only)
  public sessionSignal$ = this.sessionSignal.asReadonly();
  public userSignal$ = this.userSignal.asReadonly();
  public isAuthenticatedSignal$ = this.isAuthenticatedSignal.asReadonly();
  public isLoadingSignal$ = this.isLoadingSignal.asReadonly();
  public isEmailVerifiedSignal$ = this.isEmailVerifiedSignal.asReadonly();
  public emailVerificationRequiredSignal$ = this.emailVerificationRequiredSignal.asReadonly();
  public isOAuthSetupSignal$ = this.isOAuthSetupSignal.asReadonly();
  public farmiqIdSignal$ = this.farmiqIdSignal.asReadonly();
  
  // Token refresh timer
  private tokenRefreshTimer: NodeJS.Timeout | null = null;
  private readonly TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000; // Refresh 5 minutes before expiry

  constructor() {
    // Only initialize Supabase client in browser environment
    if (isPlatformBrowser(this.platformId)) {
      this.initializeSupabaseClient();
      this.setupSessionRecovery();
      this.setupTokenRefreshInterval();
    }
  }

  /**
   * Implement OnDestroy to clean up resources on service destruction
   */
  ngOnDestroy(): void {
    this.cleanupTokenRefreshInterval();
  }

  /**
   * Initialize Supabase client with environment credentials
   */
  private initializeSupabaseClient(): void {
    if (!environment.supabase?.url || !environment.supabase?.anonKey) {
      console.warn('⚠️ Supabase credentials not configured. Auth features will not work.');
      return;
    }
    
    try {
      this.supabase = createClient(environment.supabase.url, environment.supabase.anonKey);
    } catch (error) {
      this.errorHandlingService.handleError(error, ErrorType.SUPABASE);
    }
  }

  /**
   * Setup session recovery on app initialization
   * Restores user session from stored token
   */
  private setupSessionRecovery(): void {
    this.initializeSession().catch(error => {
      console.error('Session recovery failed:', error);
    });
  }

  /**
   * Setup automatic token refresh before expiry
   */
  private setupTokenRefreshInterval(): void {
    // ✅ FIX: Clean up any existing timer first
    this.cleanupTokenRefreshInterval();
    
    // Check token expiry every minute
    this.tokenRefreshTimer = setInterval(async () => {
      const session = this.sessionSignal();
      if (session && !this.tokenRefreshInProgressSignal()) {
        const expiresAt = session.expires_at || 0;
        const timeUntilExpiry = expiresAt * 1000 - Date.now();

        // If token expires in less than 5 minutes, refresh it
        if (timeUntilExpiry > 0 && timeUntilExpiry < this.TOKEN_REFRESH_THRESHOLD) {
          await this.refreshToken();
        }
      }
    }, 60 * 1000); // Check every minute
  }

  /**
   * Clean up token refresh interval
   * ✅ FIX: Properly clear interval and set to null
   */
  private cleanupTokenRefreshInterval(): void {
    if (this.tokenRefreshTimer !== null) {
      clearInterval(this.tokenRefreshTimer);
      this.tokenRefreshTimer = null;  // ← Must set to null!
      console.log('🧹 Token refresh interval cleaned up');
    }
  }

  /**
   * ✅ NEW: Create user profile in database after signup/OAuth login
   * Generates FarmIQ ID and stores user_profiles entry
   */
  async createUserProfile(userId: string, email: string, firstName: string, lastName: string, phoneNumber?: string): Promise<string | null> {
    try {
      // Generate unique FarmIQ ID using injected service (no duplication!)
      // Generate FarmIQ ID (uniqueness validated at database level)
      const farmiqId = this.generateFarmiqId();
      
      // Create user_profiles entry
      const { data, error } = await this.getClient()
        .from('user_profiles')
        .insert({
          id: userId,
          email: email,
          first_name: firstName,
          last_name: lastName,
          phone_number: phoneNumber || '',
          farmiq_id: farmiqId,
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        })
        .select('farmiq_id')
        .single();
      
      if (error) throw error;
      
      // Store farmiq-id in signal
      const id = data?.farmiq_id || farmiqId;
      this.farmiqIdSignal.set(id);
      
      // Also store in localStorage for recovery
      sessionStorage.setItem('farmiq_id', id);
      
      console.log(`✅ User profile created with FarmIQ ID: ${id}`);
      return id;
    } catch (error) {
      console.error('❌ Error creating user profile:', error);
      return null;
    }
  }

  /**
   * ✅ NEW: Retrieve FarmIQ ID from user_profiles table
   * Used during login to restore farmiq-id
   */
  async getFarmiqIdFromProfile(userId: string): Promise<string | null> {
    try {
      const { data, error } = await this.getClient()
        .from('user_profiles')
        .select('farmiq_id')
        .eq('id', userId)
        .maybeSingle();
      
      if (error) throw error;
      
      if (data?.farmiq_id) {
        this.farmiqIdSignal.set(data.farmiq_id);
        console.log(`✅ Retrieved FarmIQ ID: ${data.farmiq_id}`);
        return data.farmiq_id;
      }
      
      console.warn('⚠️ No FarmIQ ID found in profile, generating new one...');
      return null;
    } catch (error) {
      console.error('❌ Error retrieving FarmIQ ID:', error);
      return null;
    }
  }

  /**
   * Generate a unique FarmIQ ID (FQ + 4 random alphanumeric characters)
   * Format: FQ7K2P, FQX9M1, etc.
   * ⚠️ DEPRECATED: Use FarmiqIdService.generateUniqueId() instead
   * This method kept only for backward compatibility
   */
  async generateUniqueFarmiqId(): Promise<string> {
    return this.generateFarmiqId();
  }

  /**
   * Get the Supabase client instance
   */
  private getClient(): SupabaseClient {
    if (!this.supabase) {
      throw new Error('Supabase client not initialized. Make sure you are in a browser environment with proper credentials.');
    }
    return this.supabase;
  }

  /**
   * Get Supabase client for direct database queries
   * Used by services that need direct access to Supabase
   */
  async getSupabaseClient(): Promise<SupabaseClient> {
    if (!this.supabase) {
      throw new Error('Supabase client not initialized. Make sure you are in a browser environment with proper credentials.');
    }
    return this.supabase;
  }

  /**
   * Get auth callback URL based on environment
   * - In production: use explicit full URL from environment (`authCallbackFullUrl`) if provided
   * - Otherwise (development or missing full URL): use dynamic `window.location.origin` + `authCallbackUrl`
   */
  private getAuthCallbackUrl(): string {
    // Server-side: return relative path
    if (typeof window === 'undefined') {
      return environment.authCallbackUrl || '/auth-callback';
    }

    // If in production and an explicit full URL is configured, use it.
    const envAny = environment as any;
    if (environment.production && envAny.authCallbackFullUrl) {
      console.log('Using explicit production auth callback URL:', envAny.authCallbackFullUrl);
      return envAny.authCallbackFullUrl;
    }

    // Fallback: dynamic origin
    const origin = window.location.origin;
    const callbackPath = environment.authCallbackUrl || '/auth-callback';
    const fullUrl = `${origin}${callbackPath}`;
    console.log('Using dynamic auth callback URL:', fullUrl);
    return fullUrl;
  }

  /**
   * Initialize session from stored token
   * Sets up auth state listener for real-time session updates
   */
  private async initializeSession(): Promise<void> {
    if (!this.getClient()) return;
    
    try {
      this.isLoadingSignal.set(true);
      
      const { data, error } = await this.getClient().auth.getSession();
      if (error) throw error;

      if (data.session) {
        this.sessionSignal.set(data.session);
        this.isAuthenticatedSignal.set(true);
        if (data.session.user) {
          this.userSignal.set({
            id: data.session.user.id,
            email: data.session.user.email || '',
            user_metadata: data.session.user.user_metadata,
          } as AuthUser);
        }
        console.log('✅ Session recovered from storage');
      }

      // Listen for auth state changes (login, logout, token refresh, etc.)
      this.getClient().auth.onAuthStateChange((event, session) => {
        console.log('🔄 Auth state change event:', event);
        
        // During OAuth setup, ignore SIGNED_OUT events (they may be spurious from 401 errors)
        // Only process actual sign out if not in OAuth setup mode
        if (event === 'SIGNED_OUT' && this.isOAuthSetupSignal()) {
          console.warn('⚠️ SIGNED_OUT event during OAuth setup, ignoring...');
          // Don't clear signals during OAuth setup
          return;
        }
        
        this.sessionSignal.set(session);
        
        if (session?.user) {
          this.userSignal.set({
            id: session.user.id,
            email: session.user.email || '',
            user_metadata: session.user.user_metadata,
          } as AuthUser);
          this.isAuthenticatedSignal.set(true);
        } else {
          this.userSignal.set(null);
          this.isAuthenticatedSignal.set(false);
        }
      });

      this.isLoadingSignal.set(false);
    } catch (error) {
      this.errorHandlingService.handleError(error, ErrorType.SUPABASE);
      this.isLoadingSignal.set(false);
    }
  }

  /**
   * Refresh access token before expiry
   * Uses refresh token to get a new access token
   */
  private async refreshToken(): Promise<boolean> {
    const session = this.sessionSignal();
    if (!session?.refresh_token || this.tokenRefreshInProgressSignal()) {
      return false;
    }

    try {
      this.tokenRefreshInProgressSignal.set(true);
      console.log('🔄 Refreshing access token...');

      const { data, error } = await this.getClient().auth.refreshSession();
      
      if (error) {
        console.warn('Token refresh failed, forcing logout:', error);
        await this.signOut();
        return false;
      }

      if (data.session) {
        this.sessionSignal.set(data.session);
        console.log('✅ Token refreshed successfully');
        return true;
      }

      return false;
    } catch (error) {
      this.errorHandlingService.handleError(error, ErrorType.AUTH);
      return false;
    } finally {
      this.tokenRefreshInProgressSignal.set(false);
    }
  }

  /**
   * Sign up new user
   */
  async signUp(request: SignUpRequest): Promise<AuthResponse> {
    try {
      this.isLoadingSignal.set(true);
      
      const { data, error } = await this.getClient().auth.signUp({
        email: request.email,
        password: request.password,
        options: {
          data: {
            full_name: request.full_name,
            phone_number: request.phone_number,
          },
          emailRedirectTo: `${this.getAuthCallbackUrl()}`,
        },
      });

      if (error) throw error;

      // ✅ NEW: Create user profile with FarmIQ ID after signup
      if (data.user?.id) {
        const firstName = request.full_name?.split(' ')[0] || '';
        const lastName = request.full_name?.split(' ').slice(1).join(' ') || '';
        
        await this.createUserProfile(
          data.user.id,
          request.email,
          firstName,
          lastName,
          request.phone_number
        );
      }

      return {
        user: data.user ? {
          id: data.user.id,
          email: data.user.email || '',
          user_metadata: data.user.user_metadata,
        } as AuthUser : null,
        session: null,
      };
    } catch (error) {
      this.errorHandlingService.handleError(error, ErrorType.AUTH);
      throw error;
    } finally {
      this.isLoadingSignal.set(false);
    }
  }

  /**
   * Sign in user with email and password
   */
  async signIn(request: SignInRequest): Promise<AuthResponse> {
    try {
      this.isLoadingSignal.set(true);
      
      const { data, error } = await this.getClient().auth.signInWithPassword({
        email: request.email,
        password: request.password,
      });

      if (error) throw error;

      if (data.session) {
        this.sessionSignal.set({
          access_token: data.session.access_token,
          refresh_token: data.session.refresh_token || '',
          expires_in: data.session.expires_in || 3600,
          token_type: data.session.token_type || 'Bearer',
          user: {
            id: data.user?.id || '',
            email: data.user?.email || '',
            user_metadata: data.user?.user_metadata,
          } as any,
        });
        this.isAuthenticatedSignal.set(true);

        if (data.user) {
          this.userSignal.set({
            id: data.user.id,
            email: data.user.email || '',
            user_metadata: data.user.user_metadata,
          } as AuthUser);

          // ✅ NEW: Retrieve FarmIQ ID from profile
          await this.getFarmiqIdFromProfile(data.user.id);
        }
      }

      return {
        user: data.user ? {
          id: data.user.id,
          email: data.user.email || '',
          user_metadata: data.user.user_metadata,
        } as AuthUser : null,
        session: data.session ? {
          access_token: data.session.access_token,
          refresh_token: data.session.refresh_token || '',
          expires_in: data.session.expires_in || 3600,
          token_type: data.session.token_type || 'Bearer',
          user: {
            id: data.user?.id || '',
            email: data.user?.email || '',
            user_metadata: data.user?.user_metadata,
          } as AuthUser,
        } : null,
      };
    } catch (error) {
      this.errorHandlingService.handleError(error, ErrorType.AUTH);
      throw error;
    } finally {
      this.isLoadingSignal.set(false);
    }
  }

  /**
   * Sign out user and clear all local state
   * Removes session, user data, and stops token refresh
   */
  async signOut(): Promise<void> {
    try {
      console.log('🚪 Signing out user...');
      
      // Stop token refresh interval
      this.cleanupTokenRefreshInterval();

      // Call Supabase signOut
      const { error } = await this.getClient().auth.signOut();
      if (error) throw error;

      // Clear all signals immediately
      this.sessionSignal.set(null);
      this.userSignal.set(null);
      this.isAuthenticatedSignal.set(false);
      this.isLoadingSignal.set(false);
      this.tokenRefreshInProgressSignal.set(false);

      // Aggressively clear all storage keys that Supabase might use
      if (typeof window !== 'undefined') {
        try {
          // Clear Supabase auth tokens
          localStorage.removeItem('sb-auth-token');
          sessionStorage.removeItem('sb-auth-token');
          
          // Clear all Supabase-related keys (they typically start with 'sb-' or 'supabase-')
          const keysToRemove = [];
          for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && (key.includes('supabase') || key.includes('sb-'))) {
              keysToRemove.push(key);
            }
          }
          keysToRemove.forEach(key => localStorage.removeItem(key));
          
          // Also clear session storage
          const sessionKeysToRemove = [];
          for (let i = 0; i < sessionStorage.length; i++) {
            const key = sessionStorage.key(i);
            if (key && (key.includes('supabase') || key.includes('sb-'))) {
              sessionKeysToRemove.push(key);
            }
          }
          sessionKeysToRemove.forEach(key => sessionStorage.removeItem(key));
        } catch (e) {
          // Ignore storage errors
          console.warn('Error clearing storage:', e);
        }
      }

      console.log('✅ User signed out successfully');
    } catch (error) {
      this.errorHandlingService.handleError(error, ErrorType.AUTH);
      
      // Even if signOut fails on backend, clear local state
      this.sessionSignal.set(null);
      this.userSignal.set(null);
      this.isAuthenticatedSignal.set(false);
      
      // Still try to clear storage
      if (typeof window !== 'undefined') {
        try {
          localStorage.removeItem('sb-auth-token');
          sessionStorage.removeItem('sb-auth-token');
        } catch (e) {
          console.warn('Error clearing storage on signOut error:', e);
        }
      }
    }
  }

  /**
   * Update user profile
   */
  async updateProfile(request: UpdateProfileRequest): Promise<AuthUser | null> {
    try {
      const { data, error } = await this.getClient().auth.updateUser({
        data: {
          full_name: request.full_name,
          avatar_url: request.avatar_url,
        },
      });

      if (error) throw error;

      const user: AuthUser = {
        id: data.user!.id,
        email: data.user!.email || '',
        user_metadata: data.user!.user_metadata,
      };

      this.userSignal.set(user);
      return user;
    } catch (error) {
      console.error('Profile update error:', error);
      throw error;
    }
  }

  /**
   * Get current session
   */
  getSession(): Session | null {
    return this.sessionSignal();
  }

  /**
   * Get current user
   */
  getUser(): AuthUser | null {
    return this.userSignal();
  }

  /**
   * Get access token
   */
  getAccessToken(): string | null {
    const session = this.getSession();
    return session?.access_token || null;
  }

  /**
   * ✅ NEW: Get FarmIQ ID for request headers
   */
  getFarmiqId(): string | null {
    return this.farmiqIdSignal();
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.isAuthenticatedSignal();
  }

  /**
   * Set OAuth setup flag to prevent profile loading during initial setup
   */
  setOAuthSetup(isSetup: boolean): void {
    console.log(`🔐 OAuth setup mode: ${isSetup}`);
    this.isOAuthSetupSignal.set(isSetup);
  }

  /**
   * Check if currently in OAuth setup mode
   */
  isOAuthSetup(): boolean {
    return this.isOAuthSetupSignal();
  }

  /**
   * Get farmer profile by user ID
   */
  async getFarmerProfile(userId: string): Promise<any> {
    try {
      const { data, error } = await this.getClient()
        .from('farmer_profiles')
        .select('*')
        .eq('id', userId)
        .single();

      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error fetching farmer profile:', error);
      throw error;
    }
  }

  /**
   * Update farmer profile
   */
  async updateFarmerProfile(userId: string, updates: any): Promise<any> {
    try {
      const { data, error } = await this.getClient()
        .from('farmer_profiles')
        .update(updates)
        .eq('id', userId)
        .select()
        .single();

      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error updating farmer profile:', error);
      throw error;
    }
  }

  /**
   * Subscribe to farmer profile changes (real-time updates)
   */
  subscribeFarmerProfile(userId: string, callback: (payload: any) => void): any {
    try {
      const channel = this.getClient()
        .channel(`farmer_profiles:${userId}`)
        .on(
          'postgres_changes',
          {
            event: '*',
            schema: 'public',
            table: 'farmer_profiles',
            filter: `id=eq.${userId}`,
          },
          (payload: any) => callback(payload)
        )
        .subscribe();

      return channel;
    } catch (error) {
      console.error('Error subscribing to farmer profile:', error);
      throw error;
    }
  }

  /**
   * Send magic link for passwordless email login
   */
  async signInWithMagicLink(email: string): Promise<{ success: boolean; message: string }> {
    try {
      const { error } = await this.getClient().auth.signInWithOtp({
        email: email,
        options: {
          emailRedirectTo: `${this.getAuthCallbackUrl()}`,
        },
      });

      if (error) throw error;

      return {
        success: true,
        message: `Magic link sent to ${email}. Check your inbox.`,
      };
    } catch (error) {
      console.error('Magic link error:', error);
      throw error;
    }
  }

  /**
   * Verify OTP token (from magic link or SMS)
   */
  async verifyOtp(email: string, token: string, type: 'email' | 'sms' = 'email'): Promise<AuthResponse> {
    try {
      const { data, error } = type === 'email' 
        ? await this.getClient().auth.verifyOtp({
            email: email,
            token: token,
            type: 'email',
          })
        : await this.getClient().auth.verifyOtp({
            phone: email, // For SMS, this would be phone
            token: token,
            type: 'sms',
          });

      if (error) throw error;

      if (data.session) {
        this.sessionSignal.set({
          access_token: data.session.access_token,
          refresh_token: data.session.refresh_token || '',
          expires_in: data.session.expires_in || 3600,
          token_type: data.session.token_type || 'Bearer',
          user: {
            id: data.user?.id || '',
            email: data.user?.email || '',
            user_metadata: data.user?.user_metadata,
          } as any,
        });
        this.isAuthenticatedSignal.set(true);

        const user: AuthUser = {
          id: data.user!.id,
          email: data.user!.email || '',
          user_metadata: data.user!.user_metadata,
        };

        this.userSignal.set(user);
      }

      return {
        user: data.user ? {
          id: data.user.id,
          email: data.user.email || '',
          user_metadata: data.user.user_metadata,
        } as AuthUser : null,
        session: data.session ? {
          access_token: data.session.access_token,
          refresh_token: data.session.refresh_token || '',
          expires_in: data.session.expires_in || 3600,
          token_type: data.session.token_type || 'Bearer',
          user: {
            id: data.user?.id || '',
            email: data.user?.email || '',
            user_metadata: data.user?.user_metadata,
          } as AuthUser,
        } : null,
      };
    } catch (error) {
      console.error('OTP verification error:', error);
      throw error;
    }
  }

  /**
   * Sign up with email and password (traditional method)
   */
  async signUpWithPassword(email: string, password: string, metadata?: any): Promise<AuthResponse> {
    try {
      const { data, error } = await this.getClient().auth.signUp({
        email: email,
        password: password,
        options: {
          data: metadata,
          emailRedirectTo: `${this.getAuthCallbackUrl()}`,
        },
      });

      if (error) throw error;

      if (data.session) {
        this.sessionSignal.set({
          access_token: data.session.access_token,
          refresh_token: data.session.refresh_token || '',
          expires_in: data.session.expires_in || 3600,
          token_type: data.session.token_type || 'Bearer',
          user: {
            id: data.user?.id || '',
            email: data.user?.email || '',
            user_metadata: data.user?.user_metadata,
          } as any,
        });
        this.isAuthenticatedSignal.set(true);
      }

      return {
        user: data.user ? {
          id: data.user.id,
          email: data.user.email || '',
          user_metadata: data.user.user_metadata,
        } as AuthUser : null,
        session: data.session ? {
          access_token: data.session.access_token,
          refresh_token: data.session.refresh_token || '',
          expires_in: data.session.expires_in || 3600,
          token_type: data.session.token_type || 'Bearer',
          user: {
            id: data.user?.id || '',
            email: data.user?.email || '',
            user_metadata: data.user?.user_metadata,
          } as AuthUser,
        } : null,
      };
    } catch (error) {
      console.error('Sign up error:', error);
      throw error;
    }
  }

  /**
   * Create user profile record after signup
   * This ensures the user_profiles table has an entry before verification email is sent
   * Generates a unique FarmIQ ID and sets default role
   */
  async createUserProfileAfterSignup(
    userId: string,
    email: string,
    fullName?: string,
    phoneNumber?: string,
    farmiqId?: string
  ): Promise<{ success: boolean; farmiqId?: string }> {
    try {
      console.log(`📝 Creating user profile for user ${userId}`);

      // Use provided farmiqId or generate one
      let finalFarmiqId = farmiqId;
      
      if (!finalFarmiqId) {
        // Generate a unique FarmIQ ID (6-character alphanumeric)
        let counter = 0;
        const maxRetries = 5;
        
        while (!finalFarmiqId && counter < maxRetries) {
          const newId = Math.random()
            .toString(36)
            .substring(2, 8)
            .toUpperCase();
          
          // Check if this ID already exists
          const { data: existing } = await this.getClient()
            .from('user_profiles')
            .select('id')
            .eq('farmiq_id', newId)
            .single();
          
          if (!existing) {
            finalFarmiqId = newId;
            break;
          }
          
          counter++;
        }
        
        if (!finalFarmiqId) {
          throw new Error('Could not generate unique FarmIQ ID after retries');
        }
      }

      console.log(`🆔 Using FarmIQ ID: ${finalFarmiqId}`);

      // Create the user profile record
      const { data, error } = await this.getClient()
        .from('user_profiles')
        .insert({
          id: userId,
          email: email,
          full_name: fullName || '',
          phone_number: phoneNumber || '',
          farmiq_id: finalFarmiqId,
          primary_role: 'farmer',  // Default role
          auth_method: 'email',
          email_verified: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        })
        .select('id, farmiq_id')
        .single();

      if (error) {
        console.error('Error creating user profile:', error);
        throw new Error(`Failed to create user profile: ${error.message}`);
      }

      console.log(`✅ User profile created with FarmIQ ID: ${finalFarmiqId}`);
      
      return {
        success: true,
        farmiqId: finalFarmiqId,
      };
    } catch (error: any) {
      console.error('Error in createUserProfileAfterSignup:', error);
      return {
        success: false,
      };
    }
  }
  async getCurrentUser(): Promise<AuthUser | null> {
    try {
      const { data, error } = await this.getClient().auth.getUser();
      if (error) throw error;

      if (data.user) {
        const user: AuthUser = {
          id: data.user.id,
          email: data.user.email || '',
          user_metadata: data.user.user_metadata,
        };
        this.userSignal.set(user);
        return user;
      }

      return null;
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  }

  /**
   * Get OAuth provider from current session
   * Returns 'google', 'github', or null
   */
  async getOAuthProvider(): Promise<string | null> {
    try {
      const { data, error } = await this.getClient().auth.getUser();
      if (error || !data.user) {
        return null;
      }
      
      const provider = data.user?.app_metadata?.provider;
      console.log('OAuth provider detected:', provider);
      return provider || null;
    } catch (error) {
      console.error('Error getting OAuth provider:', error);
      return null;
    }
  }

  /**
   * Extract OAuth provider info from URL hash BEFORE session is established
   * Used during auth callback to detect OAuth early
   * This runs before getSessionFromUrl() to allow profile creation to beat effect triggers
   */
  async getOAuthProviderInfo(): Promise<{ provider: string | null }> {
    try {
      // Check URL hash for OAuth provider info
      const hash = window.location.hash || '';
      
      // Look for provider in user_metadata within the JWT
      if (hash.includes('access_token=')) {
        // JWT is present, parse it to extract provider
        const tokenMatch = hash.match(/access_token=([^&]+)/);
        if (tokenMatch) {
          const token = tokenMatch[1];
          try {
            // Decode JWT payload (don't verify signature - we just need metadata)
            const parts = token.split('.');
            if (parts.length === 3) {
              const payload = JSON.parse(atob(parts[1]));
              const provider = payload?.app_metadata?.provider || payload?.user_metadata?.oauth_provider;
              if (provider) {
                console.log('🔍 OAuth provider detected in JWT:', provider);
                return { provider };
              }
            }
          } catch (e) {
            console.warn('Could not parse JWT for provider:', e);
          }
        }
      }
      
      return { provider: null };
    } catch (error) {
      console.error('Error extracting OAuth provider info:', error);
      return { provider: null };
    }
  }

  /**
   * Check if OAuth user needs to complete profile
   * OAuth users may skip email verification step
   */
  async shouldRequireProfileCompletion(): Promise<boolean> {
    try {
      const user = this.getUser();
      if (!user) return false;
      
      const provider = await this.getOAuthProvider();
      // OAuth users might need to complete additional profile info
      return !!provider;
    } catch (error) {
      console.error('Error checking profile completion requirement:', error);
      return false;
    }
  }

  /**
   * Enforce email verification check (for security)
   * Returns true if verification is required (email/password only)
   * OAuth users skip email verification as providers handle it
   * 
   * ✅ FIX: Added caching to prevent repeated edge function calls
   * ✅ FIX: Check auth_method column to differentiate OAuth from email/password
   */
  async isEmailVerificationRequired(): Promise<boolean> {
    try {
      const user = this.getUser();
      if (!user) return false;

      // ✅ FIX: Check cache first
      const cached = this.emailVerificationCache.get(user.id);
      if (cached && cached.expiresAt > Date.now()) {
        console.log(`📦 Email verification requirement cached for ${user.id}`);
        return cached.verified;
      }

      // Check auth_method from database (set during signup)
      const { data: profile, error } = await this.getClient()
        .from('user_profiles')
        .select('auth_method, email_verified')
        .eq('id', user.id)
        .maybeSingle();

      if (error || !profile) {
        // Default: require verification for safety
        return true;
      }

      // OAuth users: email already verified by provider
      const isOAuth = profile.auth_method && ['google', 'github', 'web3'].includes(profile.auth_method);
      const requiresVerification = !isOAuth && !profile.email_verified;

      // Cache result
      this.emailVerificationCache.set(user.id, {
        verified: !requiresVerification,
        expiresAt: Date.now() + this.EMAIL_VERIFICATION_CACHE_TTL_MS,
      });

      return requiresVerification;
    } catch (error) {
      console.error('Error checking email verification requirement:', error);
      return false;
    }
  }

  /**
   * Invalidate email verification cache (call after user verifies email)
   */
  invalidateEmailVerificationCache(userId: string): void {
    this.emailVerificationCache.delete(userId);
    console.log(`🗑️ Invalidated email verification cache for ${userId}`);
  }

  /**
   * Get session from URL (after OAuth callback)
   * Handles Supabase OAuth redirect with token in hash fragment
   * CRITICAL: Sets up proper session state on OAuth redirect
   */
  async getSessionFromUrl(): Promise<Session | null> {
    try {
      // Wait a moment for Supabase to process the callback
      await new Promise(resolve => setTimeout(resolve, 100));

      // Get the current session (Supabase auto-processes the hash)
      const { data, error } = await this.getClient().auth.getSession();
      if (error) {
        console.warn('Error getting session from URL:', error);
        return null;
      }

      console.log('Session retrieved from callback:', {
        hasSession: !!data.session,
        user: data.session?.user?.email,
        provider: data.session?.user?.app_metadata?.provider,
      });

      if (data.session) {
        this.sessionSignal.set(data.session);
        this.isAuthenticatedSignal.set(true);

        if (data.session.user) {
          const user: AuthUser = {
            id: data.session.user.id,
            email: data.session.user.email || '',
            user_metadata: data.session.user.user_metadata,
          };
          this.userSignal.set(user);
          console.log('User authenticated:', user.email);
        }
      } else {
        console.warn('No session found in callback');
      }

      return data.session || null;
    } catch (error) {
      console.error('Error getting session from URL:', error);
      return null;
    }
  }

  /**
   * Send email verification link
   * Use Supabase's built-in email verification system
   */
  async sendEmailVerification(email: string): Promise<{ success: boolean; message: string }> {
    try {
      console.log('📧 Sending email verification for:', email);
      
      // Use signInWithOtp to send a verification email
      const { error } = await this.getClient().auth.signInWithOtp({
        email: email,
        options: {
          emailRedirectTo: `${this.getAuthCallbackUrl()}?type=email`,
          shouldCreateUser: false, // Don't create user, they should already exist
        },
      });

      if (error) throw error;

      return {
        success: true,
        message: `Verification email sent to ${email}. Please check your inbox.`,
      };
    } catch (error) {
      console.error('Error sending email verification:', error);
      throw error;
    }
  }

  /**
   * Check if user email is verified in Supabase Auth
   */
  async isEmailVerified(): Promise<boolean> {
    try {
      const { data, error } = await this.getClient().auth.getUser();
      if (error) throw error;
      return data.user?.email_confirmed_at ? true : false;
    } catch (error) {
      console.error('Error checking email verification status:', error);
      return false;
    }
  }

  /**
   * Get farmer's email verification status from Supabase Auth
   */
  async getFarmerVerificationStatus(): Promise<{
    email_verified: boolean;
    email_verified_at: string | null;
  }> {
    try {
      const { data, error } = await this.getClient().auth.getUser();
      if (error) throw error;
      return {
        email_verified: data.user?.email_confirmed_at ? true : false,
        email_verified_at: data.user?.email_confirmed_at || null,
      };
    } catch (error) {
      console.error('Error getting verification status:', error);
      throw error;
    }
  }

  /**
   * Update user password
   */
  async updatePassword(newPassword: string): Promise<AuthUser | null> {
    try {
      const { data, error } = await this.getClient().auth.updateUser({
        password: newPassword,
      });

      if (error) throw error;

      if (data.user) {
        const user: AuthUser = {
          id: data.user.id,
          email: data.user.email || '',
          user_metadata: data.user.user_metadata,
        };
        this.userSignal.set(user);
        return user;
      }

      return null;
    } catch (error) {
      console.error('Password update error:', error);
      throw error;
    }
  }

  /**
   * Update user email
   */
  async updateEmail(newEmail: string): Promise<AuthUser | null> {
    try {
      const { data, error } = await this.getClient().auth.updateUser(
        { email: newEmail },
        {
          emailRedirectTo: `${this.getAuthCallbackUrl()}`,
        }
      );

      if (error) throw error;

      if (data.user) {
        const user: AuthUser = {
          id: data.user.id,
          email: data.user.email || '',
          user_metadata: data.user.user_metadata,
        };
        this.userSignal.set(user);
        return user;
      }

      return null;
    } catch (error) {
      console.error('Email update error:', error);
      throw error;
    }
  }

  /**
   * Delete user account and all associated data
   */
  async deleteAccount(userId: string): Promise<{ success: boolean; message: string }> {
    try {
      // Delete farmer profile and all associated data (cascading deletes)
      const { error: farmerError } = await this.getClient()
        .from('user_profiles')
        .delete()
        .eq('id', userId);

      if (farmerError) throw farmerError;

      // Delete auth user
      const { error: authError } = await this.getClient().auth.admin.deleteUser(userId);

      if (authError) throw authError;

      // Clear local state
      this.sessionSignal.set(null);
      this.userSignal.set(null);
      this.isAuthenticatedSignal.set(false);

      return {
        success: true,
        message: 'Account deleted successfully',
      };
    } catch (error) {
      console.error('Account deletion error:', error);
      throw error;
    }
  }

  /**
   * Sign in with Google OAuth
   */
  async signInWithGoogle(): Promise<{ provider: string; url?: string }> {
    try {
      const callbackUrl = this.getAuthCallbackUrl();
      console.log('🔗 Initiating Google OAuth with callback URL:', callbackUrl);
      
      const { data, error } = await this.getClient().auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: callbackUrl,
          scopes: 'profile email',
        },
      });

      if (error) throw error;

      console.log('✅ Google OAuth URL generated:', data?.url?.substring(0, 100) + '...');

      return {
        provider: 'google',
        url: data?.url,
      };
    } catch (error) {
      console.error('Google OAuth error:', error);
      throw error;
    }
  }

  /**
   * Sign in with GitHub OAuth
   */
  async signInWithGitHub(): Promise<{ provider: string; url?: string }> {
    try {
      const callbackUrl = this.getAuthCallbackUrl();
      console.log('🔗 Initiating GitHub OAuth with callback URL:', callbackUrl);
      
      const { data, error } = await this.getClient().auth.signInWithOAuth({
        provider: 'github',
        options: {
          redirectTo: callbackUrl,
          scopes: 'user:email',
        },
      });

      if (error) throw error;

      console.log('✅ GitHub OAuth URL generated:', data?.url?.substring(0, 100) + '...');

      return {
        provider: 'github',
        url: data?.url,
      };
    } catch (error) {
      console.error('GitHub OAuth error:', error);
      throw error;
    }
  }

  /**
   * Sign in with custom Web3 wallet
   */
  async signInWithWeb3(walletAddress: string, walletType: 'metamask' | 'hashpack' = 'metamask'): Promise<AuthResponse> {
    try {
      // In a real implementation, you would:
      // 1. Generate a nonce
      // 2. Ask user to sign it with their wallet
      // 3. Verify signature and create/retrieve user
      // For now, we'll create a basic implementation

      console.log(`Web3 login attempt with ${walletType}:`, walletAddress);

      // Check if user exists with this wallet
      const { data: existingUser, error: searchError } = await this.getClient()
        .from('wallet_connections')
        .select('farmer_id')
        .eq('wallet_address', walletAddress)
        .maybeSingle();

      if (searchError) {
        console.error('Error searching for wallet:', searchError);
      }

      // For now, return a message that Web3 auth requires signature verification
      return {
        user: null,
        session: null,
      };
    } catch (error) {
      console.error('Web3 OAuth error:', error);
      throw error;
    }
  }

  /**
   * Link wallet to farmer account
   */
  async linkWallet(farmerId: string, walletAddress: string, walletType: 'metamask' | 'hashpack', network: string): Promise<any> {
    try {
      const { data, error } = await this.getClient()
        .from('wallet_connections')
        .insert({
          farmer_id: farmerId,
          wallet_address: walletAddress,
          wallet_type: walletType,
          wallet_name: walletType,
          network,
          is_primary: false,
          verified: false,
        })
        .select()
        .single();

      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error linking wallet:', error);
      throw error;
    }
  }

  /**
   * Get user's linked wallets
   */
  async getUserWallets(farmerId: string): Promise<any[]> {
    try {
      const { data, error } = await this.getClient()
        .from('wallet_connections')
        .select('*')
        .eq('farmer_id', farmerId);

      if (error) throw error;
      return data || [];
    } catch (error) {
      console.error('Error fetching wallets:', error);
      throw error;
    }
  }

  /**
   * Disconnect wallet from account
   */
  async disconnectWallet(walletId: string): Promise<{ success: boolean; message: string }> {
    try {
      const { error } = await this.getClient()
        .from('wallet_connections')
        .delete()
        .eq('id', walletId);

      if (error) throw error;

      return {
        success: true,
        message: 'Wallet disconnected successfully',
      };
    } catch (error) {
      console.error('Error disconnecting wallet:', error);
      throw error;
    }
  }

  /**
   * Create farmer profile after signup
   */
  async createFarmerProfile(
    userId: string,
    email: string,
    fullName?: string,
    phoneNumber?: string,
    avatarUrl?: string
  ): Promise<any> {
    try {
      const { data, error } = await this.getClient()
        .from('user_profiles')
        .insert({
          id: userId,
          email,
          full_name: fullName,
          phone_number: phoneNumber,
          avatar_url: avatarUrl,
        })
        .select()
        .single();

      if (error) {
        // Profile might already exist, that's okay
        if (error.code === '23505') {
          console.log('Profile already exists for user:', userId);
          return { id: userId, email };
        }
        throw error;
      }

      return data;
    } catch (error) {
      console.error('Error creating farmer profile:', error);
      throw error;
    }
  }

  /**
   * Resend email verification - Supabase Auth handles via resend
   */
  async resendEmailVerification(email: string): Promise<{ success: boolean; message: string }> {
    try {
      const { error } = await this.getClient().auth.resend({
        type: 'signup',
        email: email,
        options: {
          emailRedirectTo: `${this.getAuthCallbackUrl()}`,
        },
      });

      if (error) throw error;
      return {
        success: true,
        message: 'Verification email resent. Check your inbox.',
      };
    } catch (error) {
      console.error('Error resending verification email:', error);
      throw error;
    }
  }

  /**
   * Send password reset email
   */
  async sendPasswordReset(email: string): Promise<{ success: boolean; message: string }> {
    try {
      const { error } = await this.getClient().auth.resetPasswordForEmail(email, {
        redirectTo: `${this.getAuthCallbackUrl()}`,
      });

      if (error) throw error;

      return {
        success: true,
        message: 'Password reset email sent. Check your inbox.',
      };
    } catch (error) {
      console.error('Error sending password reset:', error);
      throw error;
    }
  }

  /**
   * Verify password reset token and update password
   */
  async resetPassword(token: string, newPassword: string): Promise<AuthUser | null> {
    try {
      const { data, error } = await this.getClient().auth.verifyOtp({
        email: '', // Email will be extracted from token
        token: token,
        type: 'recovery',
      });

      if (error) throw error;

      // Now update the password
      if (data.session) {
        this.sessionSignal.set(data.session);
        this.isAuthenticatedSignal.set(true);

        const user: AuthUser = {
          id: data.user!.id,
          email: data.user!.email || '',
          user_metadata: data.user!.user_metadata,
        };
        this.userSignal.set(user);

        // Update password
        await this.updatePassword(newPassword);
        return user;
      }

      return null;
    } catch (error) {
      console.error('Error resetting password:', error);
      throw error;
    }
  }

  /**
   * Refresh session
   */
  async refreshSession(): Promise<Session | null> {
    try {
      const { data, error } = await this.getClient().auth.refreshSession();

      if (error) throw error;

      if (data.session) {
        this.sessionSignal.set(data.session);
        return data.session;
      }

      return null;
    } catch (error) {
      console.error('Error refreshing session:', error);
      throw error;
    }
  }

  /**
   * Link OAuth identity to existing account
   * Call after user signs up/in with OAuth to create farmer profile
   */
  async linkOAuthIdentity(userId: string, email: string, provider: 'google' | 'github', fullName?: string, avatarUrl?: string): Promise<any> {
    try {
      console.log(`🔗 Linking ${provider} identity for user:`, userId);

      // Step 1: Generate unique FarmIQ ID for this user
      let farmiqId: string;
      try {
        farmiqId = await this.generateUniqueFarmiqId();
      } catch (idError) {
        console.error('⚠️ Failed to generate FarmIQ ID:', idError);
        throw idError;
      }

      console.log(`✅ Generated FarmIQ ID: ${farmiqId}`);

      // Step 2: Update Supabase auth.users metadata with FarmIQ ID
      // Store FarmIQ ID in raw_user_meta_data (Supabase auth schema)
      try {
        const { error: updateAuthError } = await this.getClient().auth.updateUser({
          data: {
            farmiq_id: farmiqId,
            full_name: fullName,
            avatar_url: avatarUrl,
            oauth_provider: provider,
          },
        });

        if (updateAuthError) {
          console.warn('⚠️ Could not update auth.users metadata:', updateAuthError);
          // Continue anyway - user_profiles will have the FarmIQ ID
        } else {
          console.log('✅ Updated auth.users metadata with FarmIQ ID');
        }
      } catch (authUpdateError) {
        console.warn('⚠️ Error updating auth user:', authUpdateError);
      }

      // Step 3: Create or update user_profiles table (denormalization for quick access)
      const { data: existing } = await this.getClient()
        .from('user_profiles')
        .select('id, full_name, avatar_url, oauth_providers, farmiq_id')
        .eq('id', userId)
        .maybeSingle();

      if (existing) {
        // Profile exists, update it
        console.log('✅ Profile exists, updating with OAuth info');
        
        // Update oauth_providers array
        const currentProviders = existing['oauth_providers'] || [];
        const updatedProviders = Array.isArray(currentProviders) ? currentProviders : [];
        if (!updatedProviders.includes(provider)) {
          updatedProviders.push(provider);
        }
        
        const { data, error } = await this.getClient()
          .from('user_profiles')
          .update({
            full_name: fullName || existing['full_name'],
            avatar_url: avatarUrl || existing['avatar_url'],
            oauth_providers: updatedProviders,
            farmiq_id: farmiqId,
            updated_at: new Date().toISOString(),
          })
          .eq('id', userId)
          .select()
          .single();

        if (error) throw error;
        console.log('✅ OAuth user profile updated');
        return data;
      } else {
        // Create new user profile
        console.log('✅ Creating new user profile for OAuth user');
        
        const { data, error } = await this.getClient()
          .from('user_profiles')
          .insert({
            id: userId,
            email,
            full_name: fullName,
            avatar_url: avatarUrl,
            oauth_providers: [provider],
            farmiq_id: farmiqId,
          })
          .select()
          .single();

        if (error) throw error;
        console.log(`✅ OAuth user profile created with FarmIQ ID: ${farmiqId}`);
        return data;
      }
    } catch (error) {
      console.error(`Error linking ${provider} identity:`, error);
      throw error;
    }
  }

  /**
   * Create OAuth user profile WITHOUT assigning a role
   * This is used in OAuth callback to create basic user profile
   * Role assignment is deferred until user selects their role in oauth-role-selection-modal component
   * 
   * @param userId - User ID from Supabase Auth
   * @param email - User email (optional)
   * @param provider - OAuth provider (google or github)
   * @param fullName - User's full name from OAuth provider
   * @param avatarUrl - User's avatar URL from OAuth provider
   * @returns User profile data
   */
  async createOAuthUserProfile(
    userId: string, 
    email: string | undefined, 
    provider: 'google' | 'github', 
    fullName?: string, 
    avatarUrl?: string
  ): Promise<any> {
    try {
      console.log(`🔗 Creating OAuth user profile (NO ROLE ASSIGNMENT) for user:`, userId);

      // Step 1: Generate unique FarmIQ ID for this user
      let farmiqId: string;
      try {
        farmiqId = await this.generateUniqueFarmiqId();
      } catch (idError) {
        console.error('⚠️ Failed to generate FarmIQ ID:', idError);
        throw idError;
      }

      console.log(`✅ Generated FarmIQ ID: ${farmiqId}`);

      // Step 2: Skip auth.updateUser during OAuth
      // The session might not be stable enough at this point
      // Instead, we'll update it through the database and edge function
      console.log('⏭️  Skipping auth.updateUser during OAuth (session stability issue)');

      // Step 3: Create or update user_profiles table
      const { data: existing } = await this.getClient()
        .from('user_profiles')
        .select('id, full_name, avatar_url, oauth_providers, farmiq_id, email')
        .eq('id', userId)
        .maybeSingle();

      if (existing) {
        // Profile exists, update it
        console.log('✅ Profile exists, updating with OAuth info');
        
        const currentProviders = existing['oauth_providers'] || [];
        const updatedProviders = Array.isArray(currentProviders) ? currentProviders : [];
        if (!updatedProviders.includes(provider)) {
          updatedProviders.push(provider);
        }
        
        const { data, error } = await this.getClient()
          .from('user_profiles')
          .update({
            full_name: fullName || existing['full_name'],
            avatar_url: avatarUrl || existing['avatar_url'],
            oauth_providers: updatedProviders,
            farmiq_id: farmiqId,
            email: email || existing['email'],
            auth_method: provider,
            updated_at: new Date().toISOString(),
          })
          .eq('id', userId)
          .select()
          .single();

        if (error) throw error;
        console.log('✅ OAuth user profile updated (no role assigned)');
        return data;
      } else {
        // Create new profile for OAuth user
        console.log('✅ Creating new user profile for OAuth user (no role assignment)');
        
        const { data, error } = await this.getClient()
          .from('user_profiles')
          .insert({
            id: userId,
            email: email || '',
            farmiq_id: farmiqId,
            full_name: fullName,
            avatar_url: avatarUrl,
            oauth_providers: [provider],
            auth_method: provider,
            primary_role: 'farmer', // Default role, will be changed during role selection
            email_verified: false, // OAuth emails are typically verified
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          })
          .select()
          .single();

        if (error) throw error;
        console.log('✅ OAuth user profile created with FarmIQ ID:', farmiqId, '(role assignment deferred)');
        return data;
      }
    } catch (error: any) {
      console.error('Error creating OAuth user profile:', error);
      throw error;
    }
  }

  /**
   * Call a Supabase Edge Function
   * @param functionName The name of the edge function to call
   * @param payload The data to send to the edge function
   * @returns The response from the edge function
   */
  async callEdgeFunction(functionName: string, payload: any): Promise<any> {
    try {
      console.log(`📞 Calling edge function: ${functionName}`, payload);
      
      // ✅ FIX: Use Supabase client's built-in functions.invoke method
      // This handles all auth complexity including OAuth tokens properly
      try {
        const { data, error } = await this.getClient().functions.invoke(functionName, {
          body: payload,
        });
        
        if (error) {
          console.error(`❌ Edge function error (${functionName}):`, error);
          throw error;
        }
        
        console.log(`✅ Edge function ${functionName} returned:`, data);
        return data;
      } catch (invokeError: any) {
        console.warn(`⚠️ Edge function invoke failed:`, invokeError.message);
        
        // If it's an auth error, try refreshing token and retrying
        if (invokeError.message?.includes('Unauthorized') || 
            invokeError.message?.includes('401') ||
            invokeError.status === 401) {
          console.warn('🔄 Auth error detected, refreshing token and retrying...');
          
          const { data, error } = await this.getClient().auth.refreshSession();
          if (error || !data.session) {
            console.error('❌ Failed to refresh token:', error);
            this.signOut();
            throw new Error('Session expired. Please sign in again.');
          }
          
          this.sessionSignal.set(data.session);
          console.log('✅ Token refreshed, retrying edge function...');
          
          // Retry with refreshed token
          const { data: retryData, error: retryError } = await this.getClient().functions.invoke(functionName, {
            body: payload,
          });
          
          if (retryError) {
            console.error(`❌ Edge function still failed after token refresh (${functionName}):`, retryError);
            throw retryError;
          }
          
          console.log(`✅ Edge function ${functionName} succeeded on retry`);
          return retryData;
        } else {
          throw invokeError;
        }
      }
    } catch (error: any) {
      // Fallback to detailed error handling
      console.error(`Error calling edge function ${functionName}:`, error);
      throw error;
    }
  }

  /**
   * DEPRECATED: Old fetch-based method, kept for reference
   * Use callEdgeFunction instead which uses Supabase client
   */
  private async callEdgeFunctionOldMethod(functionName: string, payload: any): Promise<any> {
    try {
      console.log(`📞 [OLD] Calling edge function via fetch: ${functionName}`, payload);
      
      // Ensure we have a valid, non-expired token
      let validSession = await this.ensureValidSession();
      let accessToken = validSession?.access_token;
      
      if (!accessToken) {
        throw new Error('No valid auth token available. Please log in again.');
      }
      
      const supabaseUrl = environment.supabase?.url || '';
      if (!supabaseUrl) throw new Error('Supabase URL not configured');

      console.log(`🔐 Using valid auth token for ${functionName}`);
      
      let response = await fetch(`${supabaseUrl}/functions/v1/${functionName}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      // ✅ FIX: Differentiated error handling for different status codes
      if (response.status === 401) {
        console.warn('⚠️ Edge function returned 401, attempting token refresh and retry...');
        
        // Clear any cached session first
        this.sessionSignal.set(null);
        
        // Force a token refresh
        const { data, error } = await this.getClient().auth.refreshSession();
        if (!error && data.session) {
          this.sessionSignal.set(data.session);
          validSession = data.session;
          accessToken = validSession.access_token;
          console.log('✅ Token refreshed successfully, retrying edge function call...');
          
          // Wait a small amount of time to ensure session is updated
          await new Promise(resolve => setTimeout(resolve, 100));
          
          // Retry the edge function call with fresh token
          response = await fetch(`${supabaseUrl}/functions/v1/${functionName}`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
          });
          
          if (response.ok) {
            console.log('✅ Edge function succeeded on retry with refreshed token');
          } else {
            console.warn('⚠️ Edge function still failed after token refresh:', response.status);
          }
        } else {
          console.error('❌ Failed to refresh token:', error);
          // If token refresh fails, the user needs to sign in again
          this.signOut();
          throw new Error('Session expired. Please sign in again.');
        }
      }

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`❌ Edge function error (${functionName}):`, response.status, errorText);
        
        // ✅ FIX: Provide specific error messages based on status code
        let userMessage = '';
        switch (response.status) {
          case 400:
            userMessage = `Invalid request: ${errorText}`;
            break;
          case 401:
            userMessage = 'Your session has expired. Please log in again.';
            break;
          case 403:
            userMessage = 'You do not have permission to perform this action.';
            break;
          case 404:
            userMessage = `Resource not found. Please try again later.`;
            break;
          case 429:
            userMessage = 'Too many requests. Please try again in a few minutes.';
            break;
          case 500:
          case 502:
          case 503:
            userMessage = 'Server error. Please try again later.';
            break;
          default:
            userMessage = `Request failed: ${response.status}. Please try again.`;
        }
        
        const error = new Error(userMessage);
        (error as any).statusCode = response.status;
        (error as any).context = { functionName, statusCode: response.status, errorText };
        throw error;
      }

      const data = await response.json();
      console.log(`✅ Edge function success (${functionName}):`, data);
      return data;
    } catch (error) {
      console.error(`Error calling edge function ${functionName}:`, error);
      throw error;
    }
  }

  /**
   * Handle OAuth signup flow
   * Combines OAuth authentication with farmer profile creation
   */
  async handleOAuthSignup(provider: 'google' | 'github', fullName?: string, avatarUrl?: string): Promise<any> {
    try {
      console.log(`🔐 Starting OAuth signup flow with ${provider}`);

      // Get current session (user should be authenticated after OAuth redirect)
      const { data: { user }, error: userError } = await this.getClient().auth.getUser();

      if (userError || !user) {
        throw new Error('No authenticated user found. Please complete OAuth login first.');
      }

      console.log(`✅ OAuth user authenticated:`, user.email);

      // Link identity (create/update farmer profile)
      const farmerProfile = await this.linkOAuthIdentity(
        user.id,
        user.email || '',
        provider,
        fullName || user.user_metadata?.['full_name'],
        avatarUrl || user.user_metadata?.['avatar_url']
      );

      console.log(`✅ ${provider} identity linked successfully`);

      return {
        success: true,
        user: {
          id: user.id,
          email: user.email,
          provider,
        },
        farmer: farmerProfile,
      };
    } catch (error) {
      console.error(`Error in OAuth signup:`, error);
      throw error;
    }
  }

  /**
   * ENHANCEMENT: Refresh session token if expiring soon
   * Automatically refreshes access token before expiration
   * Prevents "token expired" errors during user sessions
   */
  async ensureValidSession(): Promise<Session | null> {
    try {
      let session = this.getSession();
      
      // If no session in signal, try to recover from Supabase client directly
      if (!session) {
        console.log('🔄 No session in signal, recovering from Supabase client...');
        const { data, error } = await this.getClient().auth.getSession();
        if (error) {
          console.error('Error recovering session:', error);
          return null;
        }
        session = data.session;
        
        if (session) {
          // Update the signal with recovered session
          this.sessionSignal.set(session);
          console.log('✅ Session recovered from client');
        } else {
          console.warn('No session available in Supabase client');
          return null;
        }
      }

      // For OAuth sessions, always refresh to ensure token is valid
      // OAuth sessions sometimes have issues with the initial token
      const isOAuthSession = session.user?.app_metadata?.provider && 
                             ['google', 'github'].includes(session.user.app_metadata.provider);
      
      if (isOAuthSession) {
        console.log('🔄 OAuth session detected, force-refreshing token...');
        const { data, error } = await this.getClient().auth.refreshSession();
        
        if (error) {
          console.error('Error refreshing OAuth session:', error);
          // Continue with existing session if refresh fails
        } else if (data.session) {
          session = data.session;
          this.sessionSignal.set(session);
          console.log('✅ OAuth token refreshed');
        }
      }

      // Check if token expires in less than 5 minutes
      const expiresAt = session.expires_at ? session.expires_at * 1000 : null;
      const now = Date.now();
      const timeUntilExpiry = expiresAt ? expiresAt - now : null;

      console.log(`⏱️ Token expires in ${timeUntilExpiry ? Math.floor(timeUntilExpiry / 1000) : '?'} seconds`);

      if (timeUntilExpiry && timeUntilExpiry < 5 * 60 * 1000) {
        console.log('🔄 Token expiring soon, refreshing...');
        const { data, error } = await this.getClient().auth.refreshSession();
        
        if (error) {
          console.error('Token refresh error:', error);
          return null;
        }

        if (data.session) {
          this.sessionSignal.set(data.session);
          console.log('✅ Token refreshed successfully');
          return data.session;
        }
      }

      return session;
    } catch (error) {
      console.error('Error ensuring valid session:', error);
      return null;
    }
  }



  /**
   * ENHANCEMENT: Store current session in localStorage for persistence
   * Allows app to recover session on page refresh
   */
  private persistSessionLocally(session: Session | null): void {
    if (typeof window === 'undefined') return; // SSR check

    if (session) {
      try {
        localStorage.setItem('farmiq_session', JSON.stringify({
          accessToken: session.access_token,
          refreshToken: session.refresh_token,
          expiresAt: session.expires_at,
          timestamp: Date.now(),
        }));
      } catch (error) {
        console.warn('Could not persist session to localStorage:', error);
      }
    } else {
      try {
        localStorage.removeItem('farmiq_session');
      } catch (error) {
        console.warn('Could not clear session from localStorage:', error);
      }
    }
  }

  /**
   * ENHANCEMENT: Recover session from localStorage if available
   * Used on app initialization to restore user session
   */
  private async recoverSessionFromStorage(): Promise<void> {
    if (typeof window === 'undefined') return; // SSR check

    try {
      const stored = localStorage.getItem('farmiq_session');
      if (!stored) return;

      const { accessToken, refreshToken, timestamp } = JSON.parse(stored);
      
      // Check if stored session is reasonably recent (less than 7 days old)
      if (Date.now() - timestamp > 7 * 24 * 60 * 60 * 1000) {
        localStorage.removeItem('farmiq_session');
        return;
      }

      // Try to recover session using stored tokens
      const { data, error } = await this.getClient().auth.setSession({
        access_token: accessToken,
        refresh_token: refreshToken,
      });

      if (data.session) {
        this.sessionSignal.set(data.session);
        this.isAuthenticatedSignal.set(true);
        console.log('✅ Session recovered from storage');
      }
    } catch (error) {
      console.warn('Could not recover session from storage:', error);
      localStorage.removeItem('farmiq_session');
    }
  }

  /**
   * ENHANCEMENT: Enhanced session initialization with recovery
   * Attempts to recover session from storage before attempting auth
   */
  private async enhancedInitializeSession(): Promise<void> {
    if (!this.getClient()) return;

    try {
      // First, try to recover from localStorage
      await this.recoverSessionFromStorage();

      const { data, error } = await this.getClient().auth.getSession();
      if (error) throw error;

      if (data.session) {
        this.sessionSignal.set(data.session);
        this.isAuthenticatedSignal.set(true);
        this.persistSessionLocally(data.session);

        if (data.session.user) {
          this.userSignal.set({
            id: data.session.user.id,
            email: data.session.user.email || '',
            user_metadata: data.session.user.user_metadata,
          } as AuthUser);
        }
      }

      // Listen for auth changes
      this.getClient().auth.onAuthStateChange((event, session) => {
        this.sessionSignal.set(session);
        this.persistSessionLocally(session);

        if (session?.user) {
          this.userSignal.set({
            id: session.user.id,
            email: session.user.email || '',
            user_metadata: session.user.user_metadata,
          } as AuthUser);
          this.isAuthenticatedSignal.set(true);
        } else {
          this.userSignal.set(null);
          this.isAuthenticatedSignal.set(false);
        }
      });
    } catch (error) {
      console.error('Error in enhanced session initialization:', error);
    }
  }

  /**
   * Check if user has permission for a specific resource and action
   * Uses check-role-access-native for fine-grained access control
   * 
   * @param resource - Resource name (e.g., 'conversations', 'farms')
   * @param action - Action type (e.g., 'read', 'create', 'update')
   * @returns true if user has permission, false otherwise
   */
  async checkResourcePermission(resource: string, action: string): Promise<boolean> {
    try {
      const session = this.sessionSignal();
      if (!session?.access_token) {
        console.warn('⚠️ No session available for permission check');
        return false;
      }

      const supabaseUrl = environment.supabase?.url || 'https://tioauyhyrbqjbrypakex.supabase.co';
      
      const response = await fetch(
        `${supabaseUrl}/functions/v1/check-role-access-native`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ resource, action }),
        }
      );

      if (!response.ok) {
        console.warn(`⚠️ Permission check failed (${response.status}):`, resource, action);
        return false;
      }

      const data = await response.json();
      console.log(`✅ Permission check (${resource}/${action}):`, data.allowed ? 'ALLOWED' : 'DENIED');
      
      return data.allowed === true;
    } catch (error) {
      console.error('Error checking resource permission:', error);
      return false;
    }
  }

  /**
   * Check if user has access to a specific module
   * Uses direct database query to verify user has the required role
   * Avoids CORS issues with edge functions
   * 
   * @param roleType - Role type to check (e.g., 'farmer', 'cooperative')
   * @param module - Optional module name (e.g., 'farmgrow')
   * @returns true if user has module access, false otherwise
   */
  async checkModuleAccess(roleType: string, module?: string): Promise<boolean> {
    try {
      const session = this.sessionSignal();
      if (!session?.user?.id) {
        console.warn('⚠️ No user session available for module access check');
        return false;
      }

      // Query user_roles directly to verify the user has this role
      const { data: userRole, error } = await this.getClient()
        .from('user_roles')
        .select('id, role, is_active')
        .eq('user_id', session.user.id)
        .eq('role', roleType)
        .eq('is_active', true)
        .single();

      if (error) {
        console.warn(`⚠️ User doesn't have role "${roleType}":`, error);
        return false;
      }

      if (!userRole) {
        console.warn(`⚠️ User doesn't have role "${roleType}"`);
        return false;
      }

      // Role exists and is active, user has access to the module
      console.log(`✅ Module access check (${roleType}/${module || 'general'}): ALLOWED`);
      return true;
    } catch (error) {
      console.error('Error checking module access:', error);
      return false;
    }
  }

  /**
   * Get primary role for dashboard routing
   * This combines getting the primary role and verifying dashboard access
   * 
   * @returns Object with role and access info, or null if user has no role
   */
  /**
   * Get primary role for a user directly from database
   * The user_profiles record should exist since it's created during signup
   * If not found, provides a fallback default role
   */
  async getPrimaryRoleForUser(userId: string): Promise<string | null> {
    try {
      const { data: profile, error } = await this.getClient()
        .from('user_profiles')
        .select('primary_role')
        .eq('id', userId)
        .single();

      if (error) {
        console.warn('⚠️ Error fetching primary role:', error);
        
        // If profile doesn't exist, return default role as fallback
        // (The profile should have been created during signup)
        if (error.code === 'PGRST116' || (error as any).status === 406 || (error as any).status === 404) {
          console.warn('⚠️ Profile not found, returning default role: farmer');
          return 'farmer';  // Default fallback
        }
        
        return null;
      }

      return profile?.primary_role || null;
    } catch (error) {
      console.error('Error in getPrimaryRoleForUser:', error);
      return null;
    }
  }

  /**
   * Get primary role with access check
   * Uses database queries instead of edge functions
   */
  async getPrimaryRoleWithAccess(): Promise<{ role: string; hasAccess: boolean } | null> {
    try {
      const session = this.sessionSignal();
      if (!session?.user?.id) {
        console.warn('⚠️ No user session for role check');
        return null;
      }

      // Get primary role directly from database instead of edge function
      const role = await this.getPrimaryRoleForUser(session.user.id);

      if (!role) {
        console.warn('⚠️ No role found for user');
        return null;
      }

      // Verify module access for that role
      const hasAccess = await this.checkModuleAccess(role);

      console.log(`✅ User role: ${role}, Dashboard access: ${hasAccess}`);
      
      return {
        role: role,
        hasAccess: hasAccess,
      };
    } catch (error) {
      console.error('Error getting primary role with access:', error);
      return null;
    }
  }

  /**
   * Assign a role to a user
   * Used during signup and role selection
   */
  async assignRoleToUser(userId: string, roleType: 'farmer' | 'cooperative' | 'lender' | 'agent' | 'vendor' | 'worker' | 'admin'): Promise<void> {
    try {
      console.log(`🔄 Assigning role "${roleType}" to user ${userId}`);

      // Assign the role to the user directly in user_roles table
      const { error: assignError } = await this.getClient()
        .from('user_roles')
        .upsert({
          user_id: userId,
          role: roleType,
          is_active: true,
          assigned_at: new Date().toISOString(),
        }, { 
          onConflict: 'user_id,role' 
        });

      if (assignError) {
        console.error('Error assigning role:', assignError);
        throw new Error('Failed to assign role');
      }

      console.log(`✅ Role "${roleType}" assigned to user ${userId}`);
    } catch (error: any) {
      console.error('Error in assignRoleToUser:', error);
      throw error;
    }
  }

  /**
   * Update user's primary role
   * Called when user selects a role
   */
  async updateUserPrimaryRole(userId: string, roleType: string): Promise<void> {
    try {
      console.log(`🔄 Updating primary role to "${roleType}" for user ${userId}`);

      const { error: updateError } = await this.getClient()
        .from('user_profiles')
        .update({
          primary_role: roleType,
          updated_at: new Date().toISOString(),
        })
        .eq('id', userId);

      if (updateError) {
        console.error('Error updating profile:', updateError);
        throw new Error('Failed to update user profile');
      }

      console.log(`✅ Primary role updated to "${roleType}" for user ${userId}`);
    } catch (error: any) {
      console.error('Error in updateUserPrimaryRole:', error);
      throw error;
    }
  }

  /**
   * Get all active roles for a user
   * Public method for RoleService to query user roles
   */
  async getUserRoles(userId: string): Promise<any[]> {
    try {
      const { data: roles, error } = await this.getClient()
        .from('user_roles')
        .select('id, role, is_active, assigned_at')
        .eq('user_id', userId)
        .eq('is_active', true);

      if (error) {
        console.error('Error fetching user roles:', error);
        return [];
      }

      return roles || [];
    } catch (error) {
      console.error('Error in getUserRoles:', error);
      return [];
    }
  }

  /**
   * Check if user has a specific role
   * Public method for RoleService to verify role access
   */
  async checkUserRole(userId: string, roleType: string): Promise<boolean> {
    try {
      const { data: role, error } = await this.getClient()
        .from('user_roles')
        .select('id, role, is_active')
        .eq('user_id', userId)
        .eq('role', roleType)
        .eq('is_active', true)
        .single();

      if (error) {
        return false;
      }

      return !!role && role.is_active;
    } catch (error) {
      console.error('Error in checkUserRole:', error);
      return false;
    }
  }

  /**
   * Generate a unique FarmIQ ID
   * Format: FQ + 4 random alphanumeric characters (e.g., FQK9M2)
   * Total: 6 characters (FQ prefix + 4 random)
   * 
   * @returns FarmIQ ID string
   */
  private generateFarmiqId(): string {
    let id = this.FARMIQ_PREFIX;
    
    // Generate 4 random characters from charset
    for (let i = 0; i < this.FARMIQ_ID_LENGTH; i++) {
      const randomIndex = Math.floor(Math.random() * this.FARMIQ_CHARSET.length);
      id += this.FARMIQ_CHARSET[randomIndex];
    }
    
    return id;
  }
}