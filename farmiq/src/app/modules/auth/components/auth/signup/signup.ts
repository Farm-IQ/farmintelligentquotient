/**
 * Simplified Signup Component
 * 
 * UPDATED FLOW:
 * 1. User enters basic info: first_name, last_name, email, phone_number, password
 * 2. Account is created with no role assigned
 * 3. Auth callback detects no role and shows OAuth role selection modal
 * 4. OAuth role selection modal handles all role-specific form fields
 * 5. User is redirected to appropriate dashboard after role selection
 * 
 * This removes:
 * - All role-specific fields from signup
 * - GIS farm mapping from signup
 * - Role selection from signup
 */

import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { SupabaseService } from '../../../services/supabase';
import { OAuthService } from '../../../services/oauth.service';
import { RateLimitService } from '../../../services/rate-limit.service';

interface PasswordStrengthResult {
  strength: number;
  label: string;
  isValid: boolean;
}

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './signup.html',
  styleUrl: './signup.scss'
})
export class SignupComponent implements OnInit, OnDestroy {
  signupForm!: FormGroup;
  isLoading = false;
  isOAuthLoading = false;
  errorMessage = '';
  successMessage = '';
  showPassword = false;
  showConfirmPassword = false;
  passwordStrength = 0;
  passwordStrengthResult: PasswordStrengthResult | null = null;
  
  // OAuth properties
  isOAuthSignup = false;
  oauthProvider: 'google' | 'github' | null = null;
  oauthEmail = '';
  showVerificationNotice = false;
  
  passwordStrengthLabels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong'];

  private destroy$ = new Subject<void>();

  constructor(
    private formBuilder: FormBuilder,
    private supabase: SupabaseService,
    private oauth: OAuthService,
    private router: Router,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef,
    private rateLimit: RateLimitService
  ) {
    this.initializeForm();
  }

  /**
   * Make oauth service accessible to template
   */
  get oauthService(): OAuthService {
    return this.oauth;
  }

  ngOnInit(): void {
    this.checkOAuthCallback();
  }

  /**
   * Initialize signup form - BASIC FIELDS ONLY
   */
  private initializeForm(): void {
    this.signupForm = this.formBuilder.group({
      firstName: ['', [Validators.required, Validators.minLength(2)]],
      lastName: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      phoneNumber: ['', [Validators.required, Validators.pattern(/^\+?[0-9\s()-]{10,}$/)]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', Validators.required],
      agreeTerms: [false, Validators.requiredTrue]
    }, {
      validators: this.passwordMatchValidator
    });
  }

  /**
   * Validate that passwords match
   */
  private passwordMatchValidator(form: FormGroup): { [key: string]: any } | null {
    const password = form.get('password');
    const confirmPassword = form.get('confirmPassword');
    
    if (password && confirmPassword && password.value !== confirmPassword.value) {
      return { passwordMismatch: true };
    }
    return null;
  }

  /**
   * Check for OAuth callback parameters
   */
  private checkOAuthCallback(): void {
    this.route.queryParams
      .pipe(takeUntil(this.destroy$))
      .subscribe(params => {
        if (params['oauthProvider'] && params['oauthEmail']) {
          this.isOAuthSignup = true;
          this.oauthProvider = params['oauthProvider'];
          this.oauthEmail = params['oauthEmail'];
          this.signupForm.patchValue({
            email: this.oauthEmail
          });
          this.cdr.markForCheck();
        }
      });
  }

  /**
   * SIMPLIFIED: Email/Password Signup With No Role & Rate Limiting
   * Role selection happens in auth-callback via OAuth role selection modal
   * Implements rate limiting to prevent abuse
   */
  async onSignup(): Promise<void> {
    if (this.signupForm.invalid) {
      this.errorMessage = 'Please fill all required fields correctly';
      return;
    }

    const email = this.signupForm.get('email')?.value || '';

    // ✅ NEW: Check rate limiting for signup attempts
    if (!this.rateLimit.isSignupAllowed(email)) {
      const retryTimeMs = this.rateLimit.getSignupRetryTime(email);
      const retryTimeSec = Math.ceil(retryTimeMs / 1000);
      this.errorMessage = `❌ Too many signup attempts from this email. Please try again in ${retryTimeSec} seconds.`;
      console.warn(`🚫 Signup rate limit exceeded for ${email}`);
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    try {
      const { firstName, lastName, phoneNumber, password } = this.signupForm.value;

      // Sign up user with email/password (no role assigned yet)
      const supabaseClient = await this.supabase.getSupabaseClient();
      const { data: authData, error: authError } = await supabaseClient
        .auth
        .signUp({
          email,
          password,
          options: {
            data: {
              first_name: firstName,
              last_name: lastName,
              phone_number: phoneNumber
            }
          }
        });

      if (authError) {
        throw new Error(authError.message);
      }

      if (!authData.user) {
        throw new Error('Failed to create account');
      }

      // Create base user profile WITHOUT role (role will be assigned via OAuth modal)
      const { error: profileError } = await supabaseClient
        .from('user_profiles')
        .insert({
          id: authData.user.id,
          email,
          first_name: firstName,
          last_name: lastName,
          phone_number: phoneNumber,
          email_verified: true,
          profile_completed: false,
          // NO primary_role assigned - will be set by OAuth modal or role selection
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        });

      if (profileError && !profileError.message.includes('duplicate')) {
        await supabaseClient.auth.admin.deleteUser(authData.user.id);
        throw new Error(profileError.message);
      }

      // ✅ NEW: Record successful signup
      this.rateLimit.recordSignupAttempt(email);

      this.successMessage = 'Account created successfully!';
      
      // Redirect to dashboard/role selection after brief delay
      setTimeout(() => {
        this.router.navigate(['/dashboard']);
      }, 2000);

    } catch (error: any) {
      // ✅ NEW: Record failed signup attempt (for rate limiting)
      this.rateLimit.recordSignupAttempt(email);
      
      console.error('Signup error:', error);
      this.errorMessage = error.message || 'Failed to create account. Please try again.';
    } finally {
      this.isLoading = false;
      this.cdr.markForCheck();
    }
  }

  /**
   * Toggle password visibility
   */
  togglePasswordVisibility(field: 'password' | 'confirmPassword'): void {
    if (field === 'password') {
      this.showPassword = !this.showPassword;
    } else {
      this.showConfirmPassword = !this.showConfirmPassword;
    }
  }

  /**
   * OAuth: Sign up with Google
   */
  async signUpWithGoogle(): Promise<void> {
    this.isOAuthLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    try {
      await this.oauth.signInWithOAuth('google');
    } catch (error: any) {
      console.error('Google signup error:', error);
      this.errorMessage = error.message || 'Failed to sign up with Google. Please try again.';
      this.isOAuthLoading = false;
      this.cdr.markForCheck();
    }
  }

  /**
   * OAuth: Sign up with GitHub
   */
  async signUpWithGitHub(): Promise<void> {
    this.isOAuthLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    try {
      await this.oauth.signInWithOAuth('github');
    } catch (error: any) {
      console.error('GitHub signup error:', error);
      this.errorMessage = error.message || 'Failed to sign up with GitHub. Please try again.';
      this.isOAuthLoading = false;
      this.cdr.markForCheck();
    }
  }

  /**
   * Calculate password strength
   */
  calculatePasswordStrength(password: string): void {
    let strength = 0;
    
    if (!password) {
      this.passwordStrength = 0;
      this.passwordStrengthResult = null;
      return;
    }

    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;

    this.passwordStrength = strength;
    this.passwordStrengthResult = {
      strength: strength,
      label: this.passwordStrengthLabels[strength],
      isValid: strength >= 3
    };
  }

  /**
   * Get form field
   */
  get firstName() {
    return this.signupForm.get('firstName');
  }

  get lastName() {
    return this.signupForm.get('lastName');
  }

  get email() {
    return this.signupForm.get('email');
  }

  get phoneNumber() {
    return this.signupForm.get('phoneNumber');
  }

  get password() {
    return this.signupForm.get('password');
  }

  get confirmPassword() {
    return this.signupForm.get('confirmPassword');
  }

  get agreeTerms() {
    return this.signupForm.get('agreeTerms');
  }

  /**
   * Handle image load
   */
  onImageLoad(event: Event): void {
    const img = event.target as HTMLImageElement;
    console.log('Logo image loaded successfully:', img.src);
    img.style.opacity = '1';
  }

  /**
   * Handle image load error
   */
  onImageError(event: Event): void {
    const img = event.target as HTMLImageElement;
    console.error('Failed to load logo image from:', img.src);
    // Fallback: try alternate path
    if (!img.src.includes('fallback')) {
      img.src = '/logo.png';
      img.style.opacity = '0.5';
    }
  }

  /**
   * Navigate functions
   */
  navigateHome(): void {
    this.router.navigate(['/']);
  }

  navigateToLogin(): void {
    this.router.navigate(['/login']);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
