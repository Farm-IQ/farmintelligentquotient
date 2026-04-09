                                                                                                                                                                  import { Component, OnInit, OnDestroy, PLATFORM_ID, inject, effect } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { SupabaseService } from '../../../services/supabase';
import { OAuthService } from '../../../services/oauth.service';
import { AuthRoleService } from '../../../services/auth-role';
import { RateLimitService } from '../../../services/rate-limit.service';
import type { UserRoleType } from '../../../models';
import { EmailValidationUtil } from '../../../utils/email-validation.util';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

/**
 * Login Component
 * Handles user authentication with:
 * - Email/Password login with role-based redirect
 * - Google OAuth
 * - GitHub OAuth
 * - Rate limiting to prevent brute force attacks
 */
@Component({
  selector: 'app-login',
  imports: [CommonModule, RouterLink, ReactiveFormsModule],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class LoginComponent implements OnInit, OnDestroy {
  loginForm!: FormGroup;
  isLoading = false;
  isOAuthLoading = false;
  errorMessage = '';
  successMessage = '';
  showPassword = false;
  showUnverifiedNotice = false;
  unverifiedEmail = '';
  returnUrl = '/dashboard-fiq';
  emailValidationError = '';
  private destroy$ = new Subject<void>();
  private platformId = inject(PLATFORM_ID);

  constructor(
    private formBuilder: FormBuilder,
    private supabase: SupabaseService,
    private authRole: AuthRoleService,
    private router: Router,
    private route: ActivatedRoute,
    private oauth: OAuthService,
    private rateLimit: RateLimitService
  ) {
    this.initializeForm();

    // Check if already logged in
    effect(() => {
      const isAuth = this.supabase.isAuthenticatedSignal$();
      if (isAuth && !this.showUnverifiedNotice) {
        // User is authenticated, go to role-specific dashboard
        this.authRole.navigateToRoleDashboard();
      }
    });
  }

  ngOnInit(): void {
    // Get return URL from query params
    this.route.queryParams.pipe(takeUntil(this.destroy$)).subscribe(params => {
      this.returnUrl = params['returnUrl'] || '/dashboard-fiq';
      
      // Check for error messages from callback
      if (params['error']) {
        this.errorMessage = params['error_description'] || `Authentication error: ${params['error']}`;
      }
    });

    // Listen to email changes for validation
    this.loginForm.get('email')?.valueChanges.pipe(takeUntil(this.destroy$)).subscribe(email => {
      const validation = EmailValidationUtil.validateEmail(email);
      this.emailValidationError = validation.valid ? '' : validation.error || '';
      
      // If there's a suggestion, log it
      if (validation.suggestion) {
        console.warn(`Email suggestion: ${validation.suggestion}`);
      }
    });
  }

  private initializeForm(): void {
    this.loginForm = this.formBuilder.group({
      email: ['', [Validators.required]], // Allow temporary/test emails
      password: ['', [Validators.required, Validators.minLength(6)]]
    });
  }

  /**
   * Email/Password Login with Email Verification Check & Rate Limiting
   * Enforces email verification before granting dashboard access
   * Validates email format with typo detection
   * Implements rate limiting to prevent brute force attacks
   */
  async onLogin(): Promise<void> {
    if (this.loginForm.invalid) {
      this.errorMessage = 'Please fill in all required fields correctly';
      return;
    }

    const email = this.loginForm.get('email')?.value || '';

    // ✅ NEW: Check rate limiting
    if (!this.rateLimit.isLoginAllowed(email)) {
      const retryTimeMs = this.rateLimit.getLoginRetryTime(email);
      const retryTimeSec = Math.ceil(retryTimeMs / 1000);
      this.errorMessage = `❌ Too many login attempts. Please try again in ${retryTimeSec} seconds.`;
      console.warn(`🚫 Login rate limit exceeded for ${email}`);
      return;
    }

    // Validate email format
    const emailValidation = EmailValidationUtil.validateEmail(email);
    if (!emailValidation.valid) {
      this.errorMessage = `Email validation failed: ${emailValidation.error}`;
      if (emailValidation.suggestion) {
        this.errorMessage += `\n\nDid you mean: ${emailValidation.suggestion}?`;
      }
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';
    this.showUnverifiedNotice = false;

    try {
      const { password } = this.loginForm.value;
      const response = await this.supabase.signIn({ email, password });

      if (response.user) {
        // ✅ NEW: Record successful login (rate limit will clear)
        this.rateLimit.recordLoginAttempt(email, true);

        // CRITICAL: Check if email verification is required
        const requiresVerification = await this.supabase.isEmailVerificationRequired();
        
        if (requiresVerification) {
          // Email not verified - show notice and don't grant access
          this.unverifiedEmail = email;
          this.showUnverifiedNotice = true;
          this.errorMessage = `Your email (${email}) has not been verified yet. Please check your inbox for the verification link. ` +
                             `If you didn't receive it, please request a new verification email.`;
          
          // Sign out the unverified user
          await this.supabase.signOut();
          return;
        }

        this.successMessage = 'Login successful! Loading your dashboard...';
        
        // Load user profile with role and redirect accordingly
        this.authRole.loadUserProfile().subscribe({
          next: (profile) => {
            console.log('✅ User profile loaded, role:', profile.primary_role);
            this.authRole.navigateToRoleDashboard(profile.primary_role as UserRoleType);
          },
          error: (error) => {
            console.error('Error loading profile:', error);
            // Fallback to role dashboard (will default to farmer)
            setTimeout(() => {
              this.authRole.navigateToRoleDashboard();
            }, 1500);
          }
        });
      }
    } catch (error: any) {
      // ✅ NEW: Record failed login attempt (for rate limiting)
      this.rateLimit.recordLoginAttempt(email, false);
      
      console.error('Login error:', error);
      this.errorMessage = error.message || 'Login failed. Please check your credentials and try again.';
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * Resend verification email
   */
  async resendVerificationEmail(): Promise<void> {
    if (!this.unverifiedEmail) return;

    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    try {
      const result = await this.supabase.resendEmailVerification(this.unverifiedEmail);
      this.successMessage = result.message || 'Verification email resent! Check your inbox.';
      
      setTimeout(() => {
        this.successMessage = '';
      }, 5000);
    } catch (error: any) {
      console.error('Resend verification error:', error);
      this.errorMessage = error.message || 'Failed to resend verification email. Please try again.';
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * Helper Methods
   */
  togglePasswordVisibility(): void {
    this.showPassword = !this.showPassword;
  }

  dismissError(): void {
    this.errorMessage = '';
  }

  dismissSuccess(): void {
    this.successMessage = '';
  }

  navigateHome(): void {
    this.router.navigate(['/']);
  }

  navigateToSignup(): void {
    this.router.navigate(['/signup']);
  }

  navigateToForgotPassword(): void {
    this.router.navigate(['/forgot-password']);
  }

  /**
   * Sign in with Google OAuth
   */
  async signInWithGoogle(): Promise<void> {
    if (!isPlatformBrowser(this.platformId)) return;

    this.isOAuthLoading = true;
    this.errorMessage = '';

    try {
      await this.oauth.signInWithOAuth('google');
      // After successful OAuth, user will be redirected to callback
    } catch (error: any) {
      console.error('Google OAuth error:', error);
      this.errorMessage = 'Google login failed. Please try again or use email/password.';
      this.isOAuthLoading = false;
    }
  }

  /**
   * Sign in with GitHub OAuth
   */
  async signInWithGitHub(): Promise<void> {
    if (!isPlatformBrowser(this.platformId)) return;

    this.isOAuthLoading = true;
    this.errorMessage = '';

    try {
      await this.oauth.signInWithOAuth('github');
      // After successful OAuth, user will be redirected to callback
    } catch (error: any) {
      console.error('GitHub OAuth error:', error);
      this.errorMessage = 'GitHub login failed. Please try again or use email/password.';
      this.isOAuthLoading = false;
    }
  }

  /**
   * Form Getters
   */
  get email() {
    return this.loginForm.get('email');
  }

  get password() {
    return this.loginForm.get('password');
  }

  get isSubmitDisabled(): boolean {
    return this.isLoading || this.isOAuthLoading || this.loginForm.invalid;
  }

  onImageLoad(event: Event): void {
    const img = event.target as HTMLImageElement;
    img.style.opacity = '1';
  }

  onImageError(event: Event): void {
    const img = event.target as HTMLImageElement;
    console.error('Failed to load image:', img.src);
    img.style.opacity = '0.5';
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
