/**
 * Farmer Worker Management Component
 * Add, edit, and delete farm workers with role-based configuration
 */

import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { WorkerManagementService } from '../../../farmer/services/worker-management.service';
import { FarmWorker, FARM_WORKER_ROLES } from '../../models/worker-profile.models';

@Component({
  selector: 'app-worker-management',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="worker-management">
      <div class="management-header">
        <h2>Worker Management</h2>
        <button (click)="toggleAddForm()" class="btn-primary">
          {{ showAddForm ? 'Cancel' : '+ Add Worker' }}
        </button>
      </div>

      <!-- Add/Edit Worker Form -->
      <div *ngIf="showAddForm" class="worker-form-container">
        <h3>{{ editingWorker ? 'Edit Worker' : 'Add New Worker' }}</h3>
        <form [formGroup]="workerForm" (ngSubmit)="onSubmit()" class="worker-form">
          <div class="form-grid">
            <!-- Basic Information -->
            <div class="form-section">
              <h4>Basic Information</h4>
              
              <div class="form-group">
                <label>Full Name *</label>
                <input
                  type="text"
                  formControlName="worker_name"
                  placeholder="e.g., John Doe"
                />
              </div>

              <div class="form-group">
                <label>Phone Number</label>
                <input
                  type="tel"
                  formControlName="phone_number"
                  placeholder="e.g., +254712345678"
                />
              </div>

              <div class="form-group">
                <label>Email</label>
                <input
                  type="email"
                  formControlName="email"
                  placeholder="e.g., worker@example.com"
                />
              </div>

              <div class="form-group">
                <label>National ID</label>
                <input
                  type="text"
                  formControlName="national_id"
                  placeholder="e.g., 12345678"
                />
              </div>
            </div>

            <!-- Role & Employment -->
            <div class="form-section">
              <h4>Role & Employment</h4>
              
              <div class="form-group">
                <label>Worker Role *</label>
                <select formControlName="role">
                  <option value="">Select Role</option>
                  <option *ngFor="let role of FARM_WORKER_ROLES" [value]="role.value">
                    {{ role.label }}
                  </option>
                </select>
              </div>

              <div class="form-group">
                <label>Hire Date *</label>
                <input
                  type="date"
                  formControlName="hire_date"
                />
              </div>

              <div class="form-group">
                <label>Employment Type *</label>
                <select formControlName="employment_type">
                  <option value="">Select Type</option>
                  <option value="full_time">Full Time</option>
                  <option value="part_time">Part Time</option>
                  <option value="seasonal">Seasonal</option>
                  <option value="casual">Casual</option>
                </select>
              </div>

              <div class="form-group">
                <label>Status *</label>
                <select formControlName="status">
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="on_leave">On Leave</option>
                </select>
              </div>
            </div>

            <!-- Salary & Compensation -->
            <div class="form-section">
              <h4>Compensation</h4>
              
              <div class="form-group">
                <label>Salary Amount</label>
                <input
                  type="number"
                  formControlName="salary_amount"
                  placeholder="e.g., 15000"
                />
              </div>

              <div class="form-group">
                <label>Currency</label>
                <input
                  type="text"
                  formControlName="salary_currency"
                  placeholder="e.g., KES"
                  value="KES"
                />
              </div>
            </div>

            <!-- Emergency Contact -->
            <div class="form-section">
              <h4>Emergency Information</h4>
              
              <div class="form-group">
                <label>Emergency Contact Name</label>
                <input
                  type="text"
                  formControlName="emergency_contact"
                  placeholder="e.g., Jane Doe"
                />
              </div>

              <div class="form-group">
                <label>Emergency Phone</label>
                <input
                  type="tel"
                  formControlName="emergency_phone"
                  placeholder="e.g., +254712345678"
                />
              </div>

              <div class="form-group">
                <label>Address</label>
                <input
                  type="text"
                  formControlName="address"
                  placeholder="e.g., Kisumu, Kenya"
                />
              </div>
            </div>
          </div>

          <!-- Skills & Certifications -->
          <div class="form-section">
            <h4>Skills & Certifications</h4>
            <div class="form-group">
              <label>Skills (comma-separated)</label>
              <textarea
                formControlName="skills"
                placeholder="e.g., Crop spraying, Irrigation management, Equipment maintenance"
                rows="3"
              ></textarea>
            </div>

            <div class="form-group">
              <label>Certifications (comma-separated)</label>
              <textarea
                formControlName="certifications"
                placeholder="e.g., Pesticide applicator license, First aid certification"
                rows="3"
              ></textarea>
            </div>
          </div>

          <!-- Notes -->
          <div class="form-section">
            <div class="form-group">
              <label>Notes</label>
              <textarea
                formControlName="notes"
                placeholder="Any additional information about this worker"
                rows="3"
              ></textarea>
            </div>
          </div>

          <!-- Form Actions -->
          <div class="form-actions">
            <button type="submit" [disabled]="!workerForm.valid || isLoading" class="btn-primary">
              {{ isLoading ? 'Processing...' : (editingWorker ? 'Update Worker' : 'Add Worker') }}
            </button>
            <button type="button" (click)="toggleAddForm()" class="btn-secondary">
              Cancel
            </button>
            <button
              *ngIf="editingWorker"
              type="button"
              (click)="deleteWorker()"
              [disabled]="isLoading"
              class="btn-danger"
            >
              Delete Worker
            </button>
          </div>

          <div *ngIf="error" class="error-message">
            {{ error }}
          </div>
        </form>
      </div>

      <!-- Workers List -->
      <div class="workers-list">
        <h3>Active Workers ({{ workers.length }})</h3>
        
        <div *ngIf="workers.length === 0" class="empty-state">
          <p>No workers added yet. Click "Add Worker" to get started.</p>
        </div>

        <div *ngFor="let worker of workers" class="worker-card" (click)="selectWorker(worker)">
          <div class="worker-header">
            <h4>{{ worker.worker_name }}</h4>
            <span class="role-badge">{{ getRoleLabel(worker.role) }}</span>
          </div>
          <div class="worker-details">
            <p><strong>Employment:</strong> {{ capitalize(worker.employment_type || '') }}</p>
            <p><strong>Hire Date:</strong> {{ worker.hire_date | date: 'MMM d, y' }}</p>
            <p *ngIf="worker.phone_number"><strong>Phone:</strong> {{ worker.phone_number }}</p>
            <p *ngIf="worker.salary_amount"><strong>Salary:</strong> {{ worker.salary_amount | currency }}</p>
          </div>
          <div class="worker-actions">
            <button (click)="editWorkerForm(worker)" class="btn-edit">Edit</button>
            <button (click)="generateWorkerPassword(worker)" class="btn-password" title="Generate login password">
              🔑 Password
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .worker-management {
      padding: 20px;
    }

    .management-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 30px;
    }

    .worker-form-container {
      background: #f9f9f9;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 30px;
    }

    .form-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      margin-bottom: 20px;
    }

    .form-section {
      background: white;
      padding: 15px;
      border-radius: 6px;
      border: 1px solid #e0e0e0;
    }

    .form-section h4 {
      margin-top: 0;
      margin-bottom: 15px;
      color: #333;
      font-size: 14px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .form-group {
      margin-bottom: 15px;
    }

    .form-group label {
      display: block;
      margin-bottom: 5px;
      font-weight: 500;
      color: #555;
      font-size: 13px;
    }

    .form-group input,
    .form-group select,
    .form-group textarea {
      width: 100%;
      padding: 8px 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
      font-family: inherit;
    }

    .form-group input:focus,
    .form-group select:focus,
    .form-group textarea:focus {
      outline: none;
      border-color: #4CAF50;
      box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
    }

    .form-actions {
      display: flex;
      gap: 10px;
      margin-top: 20px;
      padding-top: 20px;
      border-top: 1px solid #e0e0e0;
    }

    .btn-primary {
      background: #4CAF50;
      color: white;
      padding: 10px 20px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 500;
    }

    .btn-primary:hover:not(:disabled) {
      background: #45a049;
    }

    .btn-primary:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .btn-secondary {
      background: #757575;
      color: white;
      padding: 10px 20px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 500;
    }

    .btn-danger {
      background: #f44336;
      color: white;
      padding: 10px 20px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 500;
    }

    .btn-danger:hover:not(:disabled) {
      background: #da190b;
    }

    .error-message {
      color: #f44336;
      padding: 10px;
      background: #ffebee;
      border-radius: 4px;
      margin-top: 10px;
    }

    .workers-list {
      margin-top: 30px;
    }

    .empty-state {
      text-align: center;
      padding: 40px;
      color: #999;
      background: #f5f5f5;
      border-radius: 8px;
    }

    .worker-card {
      background: white;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 15px;
      margin-bottom: 10px;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .worker-card:hover {
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      border-color: #4CAF50;
    }

    .worker-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }

    .worker-header h4 {
      margin: 0;
      color: #333;
    }

    .role-badge {
      background: #e3f2fd;
      color: #1976d2;
      padding: 4px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
    }

    .worker-details p {
      margin: 5px 0;
      font-size: 13px;
      color: #666;
    }

    .worker-actions {
      display: flex;
      gap: 10px;
      margin-top: 10px;
    }

    .btn-edit {
      background: #2196F3;
      color: white;
      padding: 6px 12px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
      flex: 1;
    }

    .btn-edit:hover {
      background: #0b7dda;
    }

    .btn-password {
      background: #ff9800;
      color: white;
      padding: 6px 12px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
      flex: 1;
    }

    .btn-password:hover {
      background: #f57c00;
    }
  `]
})
export class WorkerManagementComponent implements OnInit {
  FARM_WORKER_ROLES = FARM_WORKER_ROLES;

  private fb = inject(FormBuilder);
private workerService = inject(WorkerManagementService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  workerForm!: FormGroup;
  workers: FarmWorker[] = [];
  farmId: string = '';
  showAddForm = false;
  editingWorker: FarmWorker | null = null;
  isLoading = false;
  error: string | null = null;

  ngOnInit(): void {
    this.initializeForm();
    this.loadFarmId();
    this.loadWorkers();
    this.subscribeToService();
  }

  private initializeForm(): void {
    this.workerForm = this.fb.group({
      worker_name: ['', [Validators.required]],
      phone_number: [''],
      email: ['', [Validators.email]],
      national_id: [''],
      role: ['', [Validators.required]],
      hire_date: ['', [Validators.required]],
      salary_amount: [0],
      salary_currency: ['KES'],
      employment_type: ['full_time', [Validators.required]],
      status: ['active', [Validators.required]],
      emergency_contact: [''],
      emergency_phone: [''],
      address: [''],
      skills: [''],
      certifications: [''],
      notes: [''],
    });
  }

  private loadFarmId(): void {
    this.farmId = this.route.snapshot.queryParams['farmId'] || '';
  }

  private loadWorkers(): void {
    if (!this.farmId) {
      console.error('Farm ID not provided');
      return;
    }
    
    this.workerService.getWorkers(this.farmId).catch(err => {
      this.error = 'Failed to load workers: ' + err.message;
    });
  }

  private subscribeToService(): void {
    this.workerService.getWorkers$().subscribe(workers => {
      this.workers = workers;
    });

    this.workerService.getIsLoading$().subscribe(loading => {
      this.isLoading = loading;
    });

    this.workerService.getError$().subscribe(error => {
      this.error = error;
    });
  }

  toggleAddForm(): void {
    this.showAddForm = !this.showAddForm;
    if (!this.showAddForm) {
      this.editingWorker = null;
      this.initializeForm();
    }
  }

  onSubmit(): void {
    if (!this.workerForm.valid || !this.farmId) return;

    const formValue = this.workerForm.value;
    const workerData = {
      ...formValue,
      user_id: '', // Will be set from auth context
      farm_id: this.farmId,
      skills: this.parseCommaSeparated(formValue.skills),
      certifications: this.parseCommaSeparated(formValue.certifications),
    };

    if (this.editingWorker) {
      this.workerService.updateWorker(this.editingWorker.id, workerData)
        .then(() => {
          this.toggleAddForm();
          this.initializeForm();
        })
        .catch(err => this.error = err.message);
    } else {
      this.workerService.addWorker(this.farmId, workerData)
        .then(() => {
          this.toggleAddForm();
          this.initializeForm();
        })
        .catch(err => this.error = err.message);
    }
  }

  selectWorker(worker: FarmWorker): void {
    this.editWorkerForm(worker);
  }

  editWorkerForm(worker: FarmWorker): void {
    this.editingWorker = worker;
    this.workerForm.patchValue({
      worker_name: worker.worker_name,
      phone_number: worker.phone_number,
      email: worker.email,
      national_id: worker.national_id,
      role: worker.role,
      hire_date: worker.hire_date?.split('T')[0],
      salary_amount: worker.salary_amount,
      salary_currency: worker.salary_currency,
      employment_type: worker.employment_type,
      status: worker.status,
      emergency_contact: worker.emergency_contact,
      emergency_phone: worker.emergency_phone,
      address: worker.address,
      skills: worker.skills?.join(', '),
      certifications: worker.certifications?.join(', '),
      notes: worker.notes,
    });
    this.showAddForm = true;
  }

  deleteWorker(): void {
    if (!this.editingWorker) return;
    if (!confirm('Are you sure you want to delete this worker?')) return;

    this.workerService.deleteWorker(this.editingWorker.id)
      .then(() => {
        this.toggleAddForm();
        this.initializeForm();
      })
      .catch(err => this.error = err.message);
  }

  getRoleLabel(role: string): string {
    const roleConfig = FARM_WORKER_ROLES.find(r => r.value === role);
    return roleConfig ? roleConfig.label : role;
  }

  capitalize(str: string): string {
    return str.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  }

  private parseCommaSeparated(str: string): string[] {
    return str
      .split(',')
      .map((s: string) => s.trim())
      .filter((s: string) => s.length > 0);
  }

  async generateWorkerPassword(worker: FarmWorker): Promise<void> {
    try {
      const tempPassword = await this.workerService.regeneratePassword(worker.id);
      
      // Show password in a modal/alert
      const message = `
Temporary Password Generated for: ${worker.worker_name}

Password: ${tempPassword}

⚠️ IMPORTANT:
- This password is temporary
- Worker must change it on first login
- Keep this password secure
- Share this password with the worker through a secure channel

Worker ID: ${worker.id}
`;
      
      alert(message);
      
      // Optionally copy to clipboard
      if (navigator.clipboard) {
        navigator.clipboard.writeText(tempPassword);
        console.log('✅ Password copied to clipboard');
      }
    } catch (error: any) {
      this.error = 'Failed to generate password: ' + error.message;
      alert('Error: ' + error.message);
    }
  }
}
