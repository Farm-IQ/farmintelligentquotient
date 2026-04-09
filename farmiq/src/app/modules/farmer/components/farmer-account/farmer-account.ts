/**
 * Farmer Account Component - UPDATED
 * 
 * NOW HANDLES:
 * - Farm owner profile management
 * - Worker management for the farm
 * - Add new workers
 * - Display generated worker passwords
 * - Manage existing workers (deactivate, suspend, regenerate password)
 */

import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { IonIcon } from '@ionic/angular/standalone';
import { FarmerService } from '../../services/farmer.service';
import { WorkerManagementService, WorkerProfile, WorkerCreateRequest } from '../../services/worker-management.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface UserProfile {
  first_name: string;
  last_name: string;
  email: string;
  phone_number?: string;
  primary_role?: string;
  [key: string]: any;
}

interface WorkerWithPassword extends WorkerProfile {
  generatedPassword?: string;
  showPassword?: boolean;
}

@Component({
  selector: 'app-farmer-account',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, IonIcon],
  templateUrl: './farmer-account.html',
  styleUrls: ['./farmer-account.scss']
})
export class FarmerAccountComponent implements OnInit, OnDestroy {
  // Profile data
  profile: UserProfile | null = null;
  loading = true;
  saving = false;
  error: string | null = null;
  successMessage: string | null = null;
  editMode = false;
  
  // Worker management
  workers: WorkerWithPassword[] = [];
  showAddWorkerForm = false;
  addWorkerForm!: FormGroup;
  isAddingWorker = false;
  workerError: string | null = null;
  
  // New password display
  showNewPasswordAlert = false;
  newWorkerPassword = '';
  newWorkerName = '';
  passwordCopied = false;

  // Current farm (needed for worker management)
  currentFarmId: string | null = null;
  
  private destroy$ = new Subject<void>();

  constructor(
    private farmerService: FarmerService,
    private workerManagementService: WorkerManagementService,
    private formBuilder: FormBuilder
  ) {
    this.initializeAddWorkerForm();
  }

  ngOnInit(): void {
    this.loadProfile();
    this.loadCurrentFarm();
    this.loadWorkers();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Initialize add worker form
   */
  private initializeAddWorkerForm(): void {
    this.addWorkerForm = this.formBuilder.group({
      firstName: ['', [Validators.required, Validators.minLength(2)]],
      lastName: ['', [Validators.required, Validators.minLength(2)]],
      phoneNumber: ['', [Validators.required, Validators.pattern(/^\+?[0-9\s()-]{10,}$/)]],
      position: ['', Validators.required],
      contractType: ['full-time', Validators.required],
      hireDate: [new Date().toISOString().split('T')[0], Validators.required],
      nationalId: [''],
      salary: ['']
    });
  }

  /**
   * Load user profile
   */
  private loadProfile(): void {
    this.loading = true;
    this.error = null;

    this.farmerService.getProfile()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.profile = { ...data };
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load profile';
          this.loading = false;
        }
      });
  }

  /**
   * Load current farm ID
   */
  private loadCurrentFarm(): void {
    this.farmerService.getCurrentFarm()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (farm) => {
          this.currentFarmId = farm?.id || null;
          if (this.currentFarmId) {
            this.loadWorkers();
          }
        },
        error: (err) => {
          console.warn('Could not load farm ID:', err);
          this.currentFarmId = null;
        }
      });
  }

  /**
   * Load workers for the farm
   */
  private loadWorkers(): void {
    if (!this.currentFarmId) return;

    this.workerManagementService.getFarmWorkers(this.currentFarmId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (workers: any) => {
          this.workers = (workers || []).map((w: any) => ({
            ...w,
            showPassword: false,
            user_id: w.user_id || w.id,
            first_name: w.first_name || w.worker_name?.split(' ')[0] || 'Unknown',
            last_name: w.last_name || w.worker_name?.split(' ')[1] || '',
            position: w.position || 'Worker',
            password_shown: false
          }));
        },
        error: (err) => {
          console.error('Failed to load workers:', err);
          this.workers = [];
        }
      });
  }

  /**
   * Save profile changes
   */
  saveProfile(): void {
    if (!this.profile) return;

    this.saving = true;
    this.error = null;
    this.successMessage = null;

    this.farmerService.updateProfile(this.profile)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.saving = false;
          this.successMessage = 'Profile updated successfully!';
          this.editMode = false;
          setTimeout(() => {
            this.successMessage = null;
          }, 3000);
        },
        error: (err) => {
          this.error = 'Failed to update profile. Please try again.';
          this.saving = false;
        }
      });
  }

  /**
   * Toggle edit mode
   */
  toggleEditMode(): void {
    this.editMode = !this.editMode;
    if (!this.editMode) {
      this.loadProfile();
    }
  }

  /**
   * Toggle add worker form
   */
  toggleAddWorkerForm(): void {
    this.showAddWorkerForm = !this.showAddWorkerForm;
    if (!this.showAddWorkerForm) {
      this.addWorkerForm.reset({
        contractType: 'full-time',
        hireDate: new Date().toISOString().split('T')[0]
      });
      this.workerError = null;
    }
  }

  /**
   * Add new worker
   */
  async addWorker(): Promise<void> {
    if (!this.currentFarmId || this.addWorkerForm.invalid) {
      this.workerError = 'Please fill all required fields';
      return;
    }

    this.isAddingWorker = true;
    this.workerError = null;

    try {
      const request: WorkerCreateRequest = {
        farm_id: this.currentFarmId,
        first_name: this.addWorkerForm.value.firstName,
        last_name: this.addWorkerForm.value.lastName,
        phone_number: this.addWorkerForm.value.phoneNumber,
        position: this.addWorkerForm.value.position,
        contract_type: this.addWorkerForm.value.contractType,
        hire_date: this.addWorkerForm.value.hireDate,
        national_id: this.addWorkerForm.value.nationalId || undefined,
        salary: this.addWorkerForm.value.salary ? parseFloat(this.addWorkerForm.value.salary) : undefined
      };

      const result = await this.workerManagementService.createWorker(request);

      // Show password alert
      this.newWorkerPassword = result.password;
      this.newWorkerName = `${result.worker.first_name} ${result.worker.last_name}`;
      this.showNewPasswordAlert = true;
      this.passwordCopied = false;

      // Reload workers
      this.loadWorkers();

      // Reset form
      this.addWorkerForm.reset({
        contractType: 'full-time',
        hireDate: new Date().toISOString().split('T')[0]
      });

      setTimeout(() => {
        this.showNewPasswordAlert = false;
      }, 30000); // Show for 30 seconds

    } catch (error: any) {
      this.workerError = error.message || 'Failed to create worker account';
    } finally {
      this.isAddingWorker = false;
    }
  }

  /**
   * Copy password to clipboard
   */
  copyPasswordToClipboard(): void {
    navigator.clipboard.writeText(this.newWorkerPassword).then(() => {
      this.passwordCopied = true;
      setTimeout(() => {
        this.passwordCopied = false;
      }, 2000);
    });
  }

  /**
   * Close password alert
   */
  closePasswordAlert(): void {
    this.showNewPasswordAlert = false;
  }

  /**
   * Toggle password visibility for worker
   */
  toggleWorkerPassword(worker: WorkerWithPassword): void {
    if (worker.showPassword) {
      worker.showPassword = false;
    } else {
      worker.showPassword = true;
    }
  }

  /**
   * Regenerate password for existing worker
   */
  async regenerateWorkerPassword(worker: WorkerWithPassword): Promise<void> {
    if (!confirm(`Regenerate password for ${worker.first_name} ${worker.last_name}? They will need to log in with the new password.`)) {
      return;
    }

    try {
      const newPassword = await this.workerManagementService.regeneratePassword(worker.id!);
      this.newWorkerPassword = newPassword;
      this.newWorkerName = `${worker.first_name} ${worker.last_name}`;
      this.showNewPasswordAlert = true;
      this.passwordCopied = false;

      // Update worker in local list
      const index = this.workers.findIndex(w => w.id === worker.id);
      if (index >= 0) {
        this.workers[index].showPassword = false;
      }
    } catch (error: any) {
      this.error = error.message || 'Failed to regenerate password';
    }
  }

  /**
   * Deactivate worker
   */
  async deactivateWorker(worker: WorkerWithPassword): Promise<void> {
    if (!confirm(`Deactivate ${worker.first_name} ${worker.last_name}? They will not be able to log in.`)) {
      return;
    }

    try {
      await this.workerManagementService.deactivateWorker(worker.id!);
      this.loadWorkers();
      this.successMessage = 'Worker deactivated successfully';
      setTimeout(() => {
        this.successMessage = null;
      }, 3000);
    } catch (error: any) {
      this.error = error.message || 'Failed to deactivate worker';
    }
  }

  /**
   * Suspend worker
   */
  async suspendWorker(worker: WorkerWithPassword): Promise<void> {
    if (!confirm(`Suspend ${worker.first_name} ${worker.last_name}? They will not be able to log in.`)) {
      return;
    }

    try {
      await this.workerManagementService.suspendWorker(worker.id!);
      this.loadWorkers();
      this.successMessage = 'Worker suspended successfully';
      setTimeout(() => {
        this.successMessage = null;
      }, 3000);
    } catch (error: any) {
      this.error = error.message || 'Failed to suspend worker';
    }
  }

  /**
   * Reactivate worker
   */
  async reactivateWorker(worker: WorkerWithPassword): Promise<void> {
    try {
      await this.workerManagementService.reactivateWorker(worker.id!);
      this.loadWorkers();
      this.successMessage = 'Worker reactivated successfully';
      setTimeout(() => {
        this.successMessage = null;
      }, 3000);
    } catch (error: any) {
      this.error = error.message || 'Failed to reactivate worker';
    }
  }

  /**
   * Get status badge class
   */
  getStatusClass(status: string): string {
    return `status-${status}`;
  }

  /**
   * Logout
   */
  logout(): void {
    this.farmerService.logout().subscribe();
  }
}
 