import { Component, OnInit, OnDestroy, PLATFORM_ID, inject, ChangeDetectorRef, NgZone } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { isPlatformBrowser } from '@angular/common';
import { SupabaseService } from '../../../services/supabase';
import { AuthRoleService } from '../../../services/auth-role';
import { OAuthService } from '../../../services/oauth.service';
import { OAuthRoleSelectionModalComponent, RoleSelectionResult } from '../oauth-role-selection-modal/oauth-role-selection-modal';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

/**
 * Auth Callback Component - Enhanced with Role-Based Routing
 * Handles OAuth redirects from Supabase auth
 * Handles email verification confirmation
 * Manages session establishment and role-based routing after authentication
 * 
 * OAuth Flow:
 * 1. OAuth user returns from provider (Google, GitHub)
 * 2. Farmer profile is created automatically
 * 3. Check if user has a role assigned
 * 4. If no role: redirect to role selection (on signup with role selection modal)
 * 5. If role exists: redirect to role-specific dashboard
 */
@Component({
  selector: 'app-auth-callback',
  imports: [CommonModule, OAuthRoleSelectionModalComponent],
  templateUrl: './auth-callback.html',
  styleUrl: './auth-callback.scss',
})
export class AuthCallback implements OnInit, OnDestroy {
  message = 'Processing authentication...';
  isVerification = false;
  
  // ✅ FIX: OAuth role selection modal properties
  showRoleSelectionModal = false;
  oauthProvider: 'google' | 'github' = 'google';
  oauthUserEmail = '';
  
  private destroy$ = new Subject<void>();
  private platformId = inject(PLATFORM_ID);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);
  private oauth = inject(OAuthService);

  constructor(
    private router: Router,
    private supabase: SupabaseService,
    private authRole: AuthRoleService
  ) {}

  ngOnInit(): void {
    // Only run callback processing in browser, not server-side
    if (!isPlatformBrowser(this.platformId)) {
      console.log('Server-side rendering, skipping OAuth callback processing');
      return;
    }
    
    // Process OAuth callback from URL hash
    this.processCallback();
  }

  private async processCallback(): Promise<void> {
    try {
      console.log('🔐 Processing auth callback...');
      console.log('Current URL:', window.location.href);

      // ============================================================
      // Step 0: Check for OAuth Errors FIRST
      // ============================================================
      const urlParams = new URLSearchParams(window.location.search);
      const hashParams = new URLSearchParams(window.location.hash.substring(1));
      
      // Check for OAuth error in query string (from URL parameters)
      const oauthError = urlParams.get('error') || hashParams.get('error');
      if (oauthError) {
        const errorCode = urlParams.get('error_code') || hashParams.get('error_code');
        const errorDescription = urlParams.get('error_description') || hashParams.get('error_description');
        
        console.error('🚨 OAuth Error Detected:');
        console.error('  Error:', oauthError);
        console.error('  Code:', errorCode);
        console.error('  Description:', decodeURIComponent(errorDescription || ''));
        
        this.handleOAuthError(oauthError, errorCode, decodeURIComponent(errorDescription || ''));
        return;
      }

      // ============================================================
      // Step 1: Check for Email Verification
      // ============================================================
      const token = urlParams.get('token');
      const type = urlParams.get('type');

      if (token && type === 'email') {
        console.log('📧 Email verification callback detected');
        this.isVerification = true;
        await this.handleEmailVerification(token);
        return;
      }

      // ============================================================
      // Step 2: Get Session from URL
      // ============================================================
      const session = await this.supabase.getSessionFromUrl();

      if (!session?.user?.id) {
        console.warn('❌ No valid session found');
        this.handleAuthenticationFailure('No session found');
        return;
      }

      console.log('✅ Session established for user:', session.user.email);

      // ============================================================
      // Step 3: Detect OAuth Provider - Check Multiple Sources
      // ============================================================
      let oauthInfo = await this.oauth.detectOAuthProvider();

      // If detectOAuthProvider fails, try to detect from metadata or session
      if (!oauthInfo && session.user?.app_metadata?.['provider']) {
        console.log('🔗 Detected OAuth from session metadata:', session.user.app_metadata['provider']);
        oauthInfo = {
          provider: session.user.app_metadata['provider'] as 'google' | 'github',
          email: session.user.email || '',
        };
      }

      // Set flags if OAuth is detected
      if (oauthInfo) {
        console.log(`🔗 OAuth provider confirmed: ${oauthInfo.provider}`);
        this.supabase.setOAuthSetup(true);
        this.authRole.setOAuthSetup(true);
      }

      // ============================================================
      // Step 4: Handle OAuth vs Email Authentication
      // ============================================================
      if (oauthInfo) {
        console.log(`✅ Handling OAuth callback for provider: ${oauthInfo.provider}`);
        await this.handleOAuthCallback(session, oauthInfo);
      } else {
        // Check if user has a role - if not, they need to select one (new user)
        console.log('📝 No OAuth provider detected, checking for user role...');
        const userRoles = await this.checkUserRole(session.user?.id);
        
        if (userRoles.length === 0) {
          // New user without a role - show role selection instead of redirecting
          console.log('⚠️ User has no role assigned, showing role selection modal');
          this.message = 'Please select your role to continue...';
          this.cdr.markForCheck();
          // Will need to add a non-OAuth role selection modal or redirect to signup
          this.router.navigate(['/signup'], { 
            queryParams: { incomplete: 'true' } 
          }).catch(err => console.error('Navigation error:', err));
        } else {
          // User has a role - proceed with dashboard access check
          console.log(`✅ User has role(s): ${userRoles.join(', ')}`);
          await this.handleEmailAuthCallback(session);
        }
      }
    } catch (error) {
      console.error('Error processing auth callback:', error);
      this.handleAuthenticationError(error);
    }
  }

  /**
   * Handle OAuth provider errors from callback URL
   * GitHub, Google, and other OAuth providers may return error parameters
   */
  private handleOAuthError(error: string, errorCode: string | null, errorDescription: string): void {
    console.error('🚨 OAuth Provider Error Encountered');
    
    let userMessage = 'Authentication failed. ';
    let retryMessage = 'Please try again or contact support.';
    
    switch (error) {
      case 'server_error':
        if (errorCode === 'unexpected_failure' && errorDescription?.includes('exchange')) {
          // This is the GitHub code exchange failure
          console.error('⚠️ OAuth Code Exchange Failed - GitHub OAuth Configuration Issue');
          console.error('   This usually means:');
          console.error('   1. GitHub OAuth app credentials (Client ID/Secret) are incorrect in Supabase');
          console.error('   2. The Redirect URI in GitHub OAuth app does not match Supabase config');
          console.error('   3. GitHub OAuth app is not properly authorized');
          console.error('   Full error:', errorDescription);
          
          userMessage = 'GitHub authentication configuration error. ';
          retryMessage = 'Please verify GitHub OAuth settings in Supabase dashboard.';
        } else {
          userMessage = 'OAuth provider returned a server error. ';
        }
        break;
        
      case 'access_denied':
        userMessage = 'You denied access to your OAuth provider account. ';
        retryMessage = 'Please try again and grant access.';
        break;
        
      case 'invalid_scope':
        userMessage = 'OAuth provider scope is invalid. ';
        retryMessage = 'Please contact support.';
        break;
        
      default:
        userMessage = `OAuth authentication error: ${error}. `;
    }
    
    this.message = userMessage + retryMessage;
    this.cdr.markForCheck();
    
    console.log(`📝 User message: ${this.message}`);

    // Redirect to login after showing error for 3 seconds
    this.ngZone.runOutsideAngular(() => {
      setTimeout(() => {
        this.ngZone.run(() => {
          this.router.navigate(['/login'], {
            queryParams: {
              error: 'oauth_failed',
              provider: this.detectProviderFromError(),
              message: userMessage.trim(),
            },
          }).catch((err) => {
            console.error('Navigation error:', err);
          });
        });
      }, 3000);
    });
  }

  /**
   * Try to detect which OAuth provider failed from error description
   */
  private detectProviderFromError(): string {
    const currentUrl = window.location.href;
    if (currentUrl.includes('github')) return 'github';
    if (currentUrl.includes('google')) return 'google';
    return 'unknown';
  }

  /**
   * Handle OAuth authentication callback
   */
  private async handleOAuthCallback(
    session: any,
    oauthInfo: { provider: 'google' | 'github'; email: string }
  ): Promise<void> {
    try {
      console.log(`🔐 Processing ${oauthInfo.provider} OAuth callback`);

      // Create user profile if it doesn't exist (for OAuth users)
      try {
        const fullName = session.user?.user_metadata?.['full_name'] || session.user?.email?.split('@')[0] || 'User';
        const phoneNumber = session.user?.user_metadata?.['phone_number'] || '';
        const firstName = fullName.split(' ')[0];
        const lastName = fullName.split(' ').slice(1).join(' ') || '';
        
        // ✅ NEW: Use updatedupdated method name
        await this.supabase.createUserProfile(
          session.user?.id,
          session.user?.email,
          firstName,
          lastName,
          phoneNumber
        );
        console.log('✅ User profile created with FarmIQ ID for OAuth user');
      } catch (profileError: any) {
        // If profile already exists, that's fine - continue
        if (profileError?.code === '23505' || profileError?.message?.includes('duplicate')) {
          console.log('ℹ️ Profile already exists for OAuth user');
        } else {
          console.error(`⚠️ Error creating profile for ${oauthInfo.provider} user:`, profileError);
        }
      }

      // Set up OAuth provider info
      try {
        await this.oauth.setupOAuthProfile(
          session.user?.id,
          session.user?.email,
          oauthInfo.provider,
          session.user?.user_metadata?.['full_name'],
          session.user?.user_metadata?.['avatar_url']
        );
      } catch (setupError) {
        console.error(`⚠️ Error setting up ${oauthInfo.provider} profile metadata:`, setupError);
        // Continue - user is authenticated, can proceed
      }

      // Check if user already has a role assigned
      console.log('🔍 Checking if OAuth user already has a role assigned...');
      const existingRoles = await this.checkUserRole(session.user?.id);
      
      if (existingRoles.length > 0) {
        console.log(`ℹ️ OAuth user already has roles: ${existingRoles.join(', ')}`);
        // User already has a role, proceed to dashboard
        await this.handleEmailAuthCallback(session);
      } else {
        // Show role selection modal for new OAuth user without a role
        console.log(`✅ Showing role selection modal for new ${oauthInfo.provider} user`);
        this.oauthProvider = oauthInfo.provider;
        this.oauthUserEmail = session.user?.email || '';
        this.showRoleSelectionModal = true;
        this.message = `${this.oauth.getProviderDisplayName(oauthInfo.provider)} authenticated! Please select your role...`;
        this.cdr.markForCheck();
      }

      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } catch (error) {
      console.error('OAuth callback error:', error);
      throw error;
    }
  }

  /**
   * Handle email/password authentication callback
   */
  private async handleEmailAuthCallback(session: any): Promise<void> {
    try {
      console.log('📧 Processing email/password authentication callback');

      this.message = 'Authentication successful! Loading your profile...';
      this.cdr.markForCheck();

      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);

      // Load user profile and redirect
      this.ngZone.runOutsideAngular(() => {
        setTimeout(() => {
          this.ngZone.run(() => {
            this.redirectToDashboardWithAccessCheck();
          });
        }, 500);
      });
    } catch (error) {
      console.error('Email auth callback error:', error);
      throw error;
    }
  }

  /**
   * Handle authentication failure
   */
  private handleAuthenticationFailure(reason: string): void {
    console.warn(`❌ Authentication failed: ${reason}`);
    this.message = 'Authentication failed. Redirecting to login...';
    this.cdr.markForCheck();

    this.ngZone.runOutsideAngular(() => {
      setTimeout(() => {
        this.ngZone.run(() => {
          this.router.navigate(['/login']).catch((err) => {
            console.error('Navigation error:', err);
          });
        });
      }, 2000);
    });
  }

  /**
   * Handle authentication error
   */
  private handleAuthenticationError(error: any): void {
    console.error('Authentication error:', error);
    this.message = 'An error occurred during authentication. Redirecting...';
    this.cdr.markForCheck();

    this.ngZone.runOutsideAngular(() => {
      setTimeout(() => {
        this.ngZone.run(() => {
          this.router.navigate(['/login']).catch((err) => {
            console.error('Navigation error:', err);
          });
        });
      }, 2000);
    });
  }

  /**
   * ✅ FIX: Handle OAuth role selection result from modal
   */
  onRoleSelected(result: RoleSelectionResult): void {
    if (result.success) {
      console.log(`✅ Role selected via modal: ${result.role}`);
      // Modal handles navigation to dashboard, so just close it
      this.showRoleSelectionModal = false;
    } else {
      console.error('Role selection failed:', result.error);
      this.message = 'Failed to assign role. Please try again.';
      // Keep modal open for retry
    }
  }

  /**
   * ✅ FIX: Handle modal closure
   */
  onRoleSelectionClosed(): void {
    console.log('Role selection modal closed');
    this.showRoleSelectionModal = false;
    // Navigate back to login if no role was selected
    this.router.navigate(['/login']).catch(err => console.error('Navigation error:', err));
  }

  /**
   * Redirect to dashboard after verifying access
   * Uses getPrimaryRoleWithAccess() to get role and verify module access
   */
  private async redirectToDashboardWithAccessCheck(): Promise<void> {
    try {
      console.log('🔍 Checking primary role with access...');
      const roleData = await this.supabase.getPrimaryRoleWithAccess();
      
      if (!roleData) {
        console.warn('⚠️ No role found or access denied');
        this.message = 'User profile not yet complete. Please complete your registration...';
        this.cdr.markForCheck();
        this.ngZone.runOutsideAngular(() => {
          setTimeout(() => {
            this.ngZone.run(() => {
              console.log('📍 Redirecting to signup (incomplete registration)');
              this.router.navigate(['/signup'], { 
                queryParams: { incomplete: 'true' } 
              }).catch(err => console.error('Navigation error:', err));
            });
          }, 1500);
        });
        return;
      }

      if (!roleData.hasAccess) {
        console.warn(`⚠️ Access denied for role: ${roleData.role}`);
        this.message = 'You do not have access to this module. Redirecting...';
        this.cdr.markForCheck();
        this.ngZone.runOutsideAngular(() => {
          setTimeout(() => {
            this.ngZone.run(() => {
              this.router.navigate(['/login']).catch(err => console.error('Navigation error:', err));
            });
          }, 1500);
        });
        return;
      }

      // User has access, navigate to dashboard
      console.log(`✅ Verified access for role: ${roleData.role}`);
      this.authRole.navigateToRoleDashboard(roleData.role as any);
    } catch (error) {
      console.error('Error checking dashboard access:', error);
      this.message = 'An error occurred. Redirecting to login...';
      this.cdr.markForCheck();
      this.ngZone.runOutsideAngular(() => {
        setTimeout(() => {
          this.ngZone.run(() => {
            this.router.navigate(['/login']).catch(err => console.error('Navigation error:', err));
          });
        }, 1500);
      });
    }
  }

  /**
   * Check if user has a role assigned
   * Uses direct database queries instead of edge functions
   */
  private async checkUserRole(userId?: string): Promise<any[]> {
    try {
      if (!userId) {
        const session = await this.supabase.getSession();
        userId = session?.user?.id;
      }

      if (!userId) {
        console.warn('❌ No user ID available for role check');
        return [];
      }

      // Query user_roles directly from database instead of edge function
      const client = await this.supabase.getSupabaseClient();
      const { data: userRoles, error } = await client
        .from('user_roles')
        .select('role')
        .eq('user_id', userId)
        .eq('is_active', true);

      if (error) {
        console.error('Error checking user roles:', error);
        return [];
      }

      const roles = (userRoles || []).map(ur => ur.role);
      console.log('✅ User roles retrieved:', roles);
      return roles;
    } catch (error) {
      console.error('Error checking user role:', error);
      return [];
    }
  }

  /**
   * Handle email verification from confirmation link
   */
  private async handleEmailVerification(token: string): Promise<void> {
    try {
      console.log('📧 Processing email verification...');
      
      // The session should be available after verification
      const session = await this.supabase.getSessionFromUrl();

      if (session && session.user) {
        // Email verification is handled by Supabase Auth automatically
        // No need to manually update database
        console.log('✅ Email verified successfully by Supabase Auth');
        
        this.message = 'Email verified successfully! Loading your profile...';
        this.cdr.markForCheck();
        
        // Clean up URL to remove query parameters with tokens
        window.history.replaceState({}, document.title, window.location.pathname);
        
        // ✅ FIX: Wait for user profile to load before navigating
        // This ensures the edge function call has a valid session
        this.ngZone.runOutsideAngular(() => {
          setTimeout(() => {
            this.ngZone.run(() => {
              // Load user profile which fetches their role
              this.authRole.loadUserProfile().subscribe({
                next: (profile) => {
                  console.log('✅ User profile loaded, role:', profile.primary_role);
                  this.message = 'Redirecting to your dashboard...';
                  this.cdr.markForCheck();
                  
                  setTimeout(() => {
                    console.log('🎯 Redirecting verified user to role-specific dashboard');
                    this.authRole.navigateToRoleDashboard(profile.primary_role as any);
                  }, 500);
                },
                error: (error) => {
                  console.error('Error loading user profile:', error);
                  this.message = 'Error loading profile. Redirecting to login...';
                  this.cdr.markForCheck();
                  
                  setTimeout(() => {
                    this.router.navigate(['/login']);
                  }, 1500);
                }
              });
            });
          }, 1000);
        });
      } else {
        console.warn('⚠️ Email verification link expired');
        this.message = 'Verification link expired. Please sign in again.';
        this.cdr.markForCheck();
        this.ngZone.runOutsideAngular(() => {
          setTimeout(() => {
            this.ngZone.run(() => {
              this.router.navigate(['/login']);
            });
          }, 2000);
        });
      }
    } catch (error) {
      console.error('Error verifying email:', error);
      this.message = 'Email verification failed. Please try again.';
      this.cdr.markForCheck();
      this.ngZone.runOutsideAngular(() => {
        setTimeout(() => {
          this.ngZone.run(() => {
            this.router.navigate(['/login']);
          });
        }, 2000);
      });
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
