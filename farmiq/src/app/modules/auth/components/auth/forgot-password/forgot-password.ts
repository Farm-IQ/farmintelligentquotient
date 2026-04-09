import { Component, OnInit, OnDestroy, PLATFORM_ID, inject, effect } from '@angular/core';
import { CommonModule, NgOptimizedImage, isPlatformBrowser } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { SupabaseService } from '../../../services/supabase';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

/**
 * Forgot Password Component
 * Handles password reset flow:
 * 1. User enters email
 * 2. Reset email sent
 * 3. User clicks reset link in email
 * 4. User enters new password
 * 5. Password updated
 */
@Component({
  selector: 'app-forgot-password',
  imports: [CommonModule, ReactiveFormsModule, NgOptimizedImage, RouterLink],
  templateUrl: './forgot-password.html',
  styleUrl: './forgot-password.scss',
})
export class ForgotPasswordComponent implements OnInit, OnDestroy {
  emailForm!: FormGroup;
  resetPasswordForm!: FormGroup;
  
  isLoading = false;
  errorMessage = '';
  successMessage = '';
  showPassword = false;
  showConfirmPassword = false;
  
  step: 'request' | 'reset' = 'request'; // Which step of process
  resetToken: string | null = null;
  resetEmail: string = '';
  
  private destroy$ = new Subject<void>();
  private platformId = inject(PLATFORM_ID);

  constructor(
    private formBuilder: FormBuilder,
    private supabase: SupabaseService,
    private router: Router
  ) {
    this.initializeForms();

    // Check if user is already authenticated
    effect(() => {
      const isAuth = this.supabase.isAuthenticatedSignal$();
      if (isAuth) {
        // Redirect authenticated users to dashboard
        this.router.navigate(['/dashboard-fiq']);
      }
    });
  }

  ngOnInit(): void {
    if (!isPlatformBrowser(this.platformId)) return;

    // Check URL for reset token (from email link)
    const url = new URL(window.location.href);
    const token = url.searchParams.get('token');
    
    if (token) {
      this.resetToken = token;
      this.step = 'reset';
      this.successMessage = 'Enter your new password below.';
    }
  }

  private initializeForms(): void {
    // Step 1: Request password reset
    this.emailForm = this.formBuilder.group({
      email: ['', [Validators.required]] // Allow temporary/test emails
    });

    // Step 2: Reset password with token
    this.resetPasswordForm = this.formBuilder.group({
      newPassword: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', Validators.required],
    }, { validators: this.passwordMatchValidator });
  }

  /**
   * Validate that passwords match
   */
  private passwordMatchValidator(control: any): any {
    const newPassword = control.get('newPassword');
    const confirmPassword = control.get('confirmPassword');

    if (!newPassword || !confirmPassword) {
      return null;
    }

    return newPassword.value === confirmPassword.value ? null : { passwordMismatch: true };
  }

  /**
   * Step 1: Request password reset email
   */
  async requestReset(): Promise<void> {
    if (this.emailForm.invalid) {
      this.errorMessage = 'Please enter a valid email address';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    try {
      const { email } = this.emailForm.value;
      this.resetEmail = email;

      const result = await this.supabase.sendPasswordReset(email);
      
      this.successMessage = result.message || `Password reset email sent to ${email}. Check your inbox and click the reset link.`;
      this.emailForm.reset();
      
      // Don't automatically change step - let user check email
    } catch (error: any) {
      console.error('Password reset request error:', error);
      this.errorMessage = error.message || 'Failed to send password reset email. Please try again.';
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * Step 2: Reset password with token
   */
  async resetPassword(): Promise<void> {
    if (this.resetPasswordForm.invalid) {
      this.errorMessage = 'Please check your password entries';
      return;
    }

    if (!this.resetToken) {
      this.errorMessage = 'Reset token is missing. Please use the reset link from your email.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    try {
      const { newPassword } = this.resetPasswordForm.value;
      
      await this.supabase.resetPassword(this.resetToken, newPassword);
      
      this.successMessage = 'Password reset successfully! Redirecting to login...';
      this.resetPasswordForm.reset();
      
      setTimeout(() => {
        this.router.navigate(['/login']);
      }, 2000);
    } catch (error: any) {
      console.error('Password reset error:', error);
      this.errorMessage = error.message || 'Failed to reset password. The reset link may have expired. Please request a new one.';
      
      // Reset to request step
      this.step = 'request';
      this.resetToken = null;
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * Helper methods
   */
  togglePasswordVisibility(field: 'password' | 'confirmPassword'): void {
    if (field === 'password') {
      this.showPassword = !this.showPassword;
    } else if (field === 'confirmPassword') {
      this.showConfirmPassword = !this.showConfirmPassword;
    }
  }

  dismissError(): void {
    this.errorMessage = '';
  }

  dismissSuccess(): void {
    this.successMessage = '';
  }

  navigateToLogin(): void {
    this.router.navigate(['/login']);
  }

  navigateToSignup(): void {
    this.router.navigate(['/signup']);
  }

  /**
   * Form getters
   */
  get email() {
    return this.emailForm.get('email');
  }

  get newPassword() {
    return this.resetPasswordForm.get('newPassword');
  }

  get confirmPassword() {
    return this.resetPasswordForm.get('confirmPassword');
  }

  /**
   * Handle image load event
   */
  onImageLoad(event: Event): void {
    const img = event.target as HTMLImageElement;
    img.style.opacity = '1';
  }

  /**
   * Handle image load error
   */
  onImageError(event: Event): void {
    const img = event.target as HTMLImageElement;
    console.error('Failed to load image:', img.src);
    img.style.opacity = '0.5';
  }

  navigateHome(): void {
    this.router.navigate(['/']);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
