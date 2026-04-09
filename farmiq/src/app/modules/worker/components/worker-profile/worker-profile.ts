/**
 * Worker Profile Component
 * Manage worker profile and password
 */

import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { SupabaseService } from '../../../auth/services/supabase';

@Component({
  selector: 'app-worker-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './worker-profile.html',
  styleUrls: ['./worker-profile.scss']
})
export class WorkerProfileComponent implements OnInit {
  passwordForm!: FormGroup;
  isLoading = false;
  error: string | null = null;
  success: string | null = null;

  private fb = inject(FormBuilder);
  private supabase = inject(SupabaseService);

  ngOnInit(): void {
    this.initializeForm();
  }

  private initializeForm(): void {
    this.passwordForm = this.fb.group(
      {
        currentPassword: ['', [Validators.required, Validators.minLength(6)]],
        newPassword: ['', [Validators.required, Validators.minLength(6)]],
        confirmPassword: ['', [Validators.required, Validators.minLength(6)]],
      },
      { validators: this.passwordMatchValidator }
    );
  }

  private passwordMatchValidator(group: FormGroup): { [key: string]: any } | null {
    const password = group.get('newPassword')?.value;
    const confirmPassword = group.get('confirmPassword')?.value;

    if (password && confirmPassword && password !== confirmPassword) {
      return { passwordMismatch: true };
    }

    return null;
  }

  async onChangePassword(): Promise<void> {
    if (!this.passwordForm.valid) return;

    this.isLoading = true;
    this.error = null;
    this.success = null;

    try {
      const supabaseClient = await this.supabase.getSupabaseClient();
      const { data: { user }, error: authError } = await supabaseClient.auth.getUser();
      
      if (authError || !user) throw new Error('Not authenticated');

      const { newPassword } = this.passwordForm.value;

      const { error: updateError } = await supabaseClient.auth.updateUser({
        password: newPassword
      });

      if (updateError) throw updateError;

      this.success = 'Password changed successfully!';
      this.passwordForm.reset();

      // Clear message after 3 seconds
      setTimeout(() => {
        this.success = null;
      }, 3000);
    } catch (err: any) {
      this.error = err.message || 'Failed to change password';
    } finally {
      this.isLoading = false;
    }
  }
}
