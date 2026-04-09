/**
 * Worker Payroll Manager Component
 * Manage worker salaries, deductions, and payment records
 */

import { Component, Input, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { WorkerManagementService } from '../../../farmer/services/worker-management.service';
import { FarmWorker, WorkerPayroll } from '../../models/worker-profile.models';

@Component({
  selector: 'app-worker-payroll-manager',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="payroll-manager">
      <!-- Salary Information -->
      <div class="salary-section">
        <h3>Salary Information</h3>
        <div class="salary-info-grid">
          <div class="info-card">
            <label>Base Salary</label>
            <div class="amount">{{ selectedWorker?.salary_amount | currency }}</div>
            <small>per month</small>
          </div>
          <div class="info-card">
            <label>Total Earned (YTD)</label>
            <div class="amount">{{ totalEarned | currency }}</div>
            <small>Year to date</small>
          </div>
          <div class="info-card">
            <label>Total Paid (YTD)</label>
            <div class="amount">{{ totalPaid | currency }}</div>
            <small>Year to date</small>
          </div>
          <div class="info-card">
            <label>Outstanding Balance</label>
            <div class="amount" [class.negative]="outstandingBalance < 0">
              {{ outstandingBalance | currency }}
            </div>
            <small>Amount owed</small>
          </div>
        </div>
      </div>

      <!-- Create Payroll Form -->
      <div class="form-section">
        <h3>Create Payroll</h3>
        <form [formGroup]="payrollForm" (ngSubmit)="createPayroll()" class="payroll-form">
          <div class="form-grid">
            <div class="form-group">
              <label>Month/Period</label>
              <input type="month" formControlName="payroll_month" />
            </div>
            <div class="form-group">
              <label>Base Salary</label>
              <input type="number" formControlName="base_salary" />
            </div>
            <div class="form-group">
              <label>Bonus</label>
              <input type="number" formControlName="bonus" placeholder="0" />
            </div>
            <div class="form-group">
              <label>Allowance</label>
              <input type="number" formControlName="allowance" placeholder="0" />
            </div>
          </div>

          <div class="form-grid">
            <div class="form-group">
              <label>Deduction (Tax)</label>
              <input type="number" formControlName="tax_deduction" placeholder="0" />
            </div>
            <div class="form-group">
              <label>Deduction (Insurance)</label>
              <input type="number" formControlName="insurance_deduction" placeholder="0" />
            </div>
            <div class="form-group">
              <label>Deduction (Other)</label>
              <input type="number" formControlName="other_deduction" placeholder="0" />
            </div>
          </div>

          <div class="form-group">
            <label>Notes</label>
            <textarea formControlName="notes" rows="2"></textarea>
          </div>

          <!-- Payroll Summary -->
          <div class="payroll-summary">
            <div class="summary-row">
              <span>Base Salary:</span>
              <span>{{ baseSalary | currency }}</span>
            </div>
            <div class="summary-row">
              <span>Bonus:</span>
              <span>{{ bonus | currency }}</span>
            </div>
            <div class="summary-row">
              <span>Allowance:</span>
              <span>{{ allowance | currency }}</span>
            </div>
            <div class="summary-row total">
              <span>Gross Pay:</span>
              <span>{{ grossPay | currency }}</span>
            </div>
            <div class="summary-row">
              <span>Tax Deduction:</span>
              <span class="deduction">-{{ taxDeduction | currency }}</span>
            </div>
            <div class="summary-row">
              <span>Insurance:</span>
              <span class="deduction">-{{ insuranceDeduction | currency }}</span>
            </div>
            <div class="summary-row">
              <span>Other Deductions:</span>
              <span class="deduction">-{{ otherDeduction | currency }}</span>
            </div>
            <div class="summary-row net-pay">
              <span>Net Pay:</span>
              <span>{{ netPay | currency }}</span>
            </div>
          </div>

          <button type="submit" [disabled]="!payrollForm.valid || isLoading" class="btn-primary">
            {{ isLoading ? 'Processing...' : 'Create Payroll' }}
          </button>
          <div *ngIf="error" class="error-message">{{ error }}</div>
          <div *ngIf="success" class="success-message">Payroll created successfully</div>
        </form>
      </div>

      <!-- Payroll History -->
      <div class="history-section">
        <h3>Payroll History</h3>
        <div class="payroll-list">
          <div *ngIf="payrollHistory.length === 0" class="empty-state">
            No payroll records yet
          </div>
          <div *ngFor="let payroll of payrollHistory" class="payroll-card">
            <div class="payroll-header">
              <div class="payroll-period">Month</div>
              <div class="payroll-status" [ngClass]="'status-pending'">
                PENDING
              </div>
            </div>
            <div class="payroll-details">
              <div class="detail-row">
                <span>Gross Pay:</span>
                <span class="amount">{{ payroll.gross_pay | currency }}</span>
              </div>
              <div class="detail-row">
                <span>Deductions:</span>
                <span class="amount">{{ calculateTotalDeductions(payroll) | currency }}</span>
              </div>
              <div class="detail-row net">
                <span>Net Pay:</span>
                <span class="amount">{{ payroll.net_pay | currency }}</span>
              </div>
            </div>
            <div class="payroll-actions">
              <button (click)="markAsPaid(payroll)" class="btn-small btn-success">
                Mark as Paid
              </button>
              <button (click)="viewPayslip(payroll)" class="btn-small btn-info">View Payslip</button>
              <button (click)="downloadPayslip(payroll)" class="btn-small btn-download">Download</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Payment Tracking -->
      <div class="payment-section">
        <h3>Payment Records</h3>
        <div class="payment-list">
          <div *ngIf="paymentRecords.length === 0" class="empty-state">
            No payments recorded yet
          </div>
          <div *ngFor="let payment of paymentRecords" class="payment-record">
            <div class="payment-date">{{ payment.payment_date | date: 'MMM d, y' }}</div>
            <div class="payment-amount">{{ payment.amount | currency }}</div>
            <div class="payment-method">{{ capitalize(payment.payment_method) }}</div>
            <div class="payment-status\" [ngClass]=\"'status-' + (payment.status || 'pending')\">
              {{ capitalize(payment.status || 'pending') }}
            </div>
            <div *ngIf="payment.notes" class="payment-notes">{{ payment.notes }}</div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .payroll-manager {
      padding: 20px;
    }

    .salary-section, .form-section, .history-section, .payment-section {
      background: white;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 20px;
      border: 1px solid #e0e0e0;
    }

    h3 {
      margin-top: 0;
      margin-bottom: 15px;
      color: #333;
    }

    .salary-info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
    }

    .info-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 8px;
      text-align: center;
    }

    .info-card label {
      font-size: 12px;
      text-transform: uppercase;
      opacity: 0.9;
      margin-bottom: 10px;
      display: block;
    }

    .amount {
      font-size: 24px;
      font-weight: bold;
      margin-bottom: 5px;
    }

    .amount.negative {
      color: #ff6b6b;
    }

    .info-card small {
      font-size: 11px;
      opacity: 0.8;
    }

    .form-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 15px;
      margin-bottom: 15px;
    }

    .form-group {
      display: flex;
      flex-direction: column;
    }

    .form-group label {
      margin-bottom: 5px;
      font-weight: 500;
      color: #555;
      font-size: 13px;
    }

    .form-group input,
    .form-group textarea {
      padding: 8px 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
    }

    .form-group input:focus,
    .form-group textarea:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
    }

    .payroll-summary {
      background: #f9f9f9;
      padding: 15px;
      border-radius: 6px;
      margin: 15px 0;
      border-left: 4px solid #667eea;
    }

    .summary-row {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid #e0e0e0;
      font-size: 14px;
    }

    .summary-row.total {
      border-bottom: 2px solid #667eea;
      font-weight: 600;
      background: #f0f0f0;
      padding: 10px;
      margin: 5px -15px 5px -15px;
      border-left: 4px solid #667eea;
    }

    .summary-row.net-pay {
      border-bottom: none;
      font-weight: 700;
      font-size: 16px;
      color: #4CAF50;
      background: #e8f5e9;
      padding: 10px;
      margin: 5px -15px -15px -15px;
      border-radius: 0 0 6px 6px;
    }

    .deduction {
      color: #f44336;
      font-weight: 500;
    }

    .btn-primary {
      background: #667eea;
      color: white;
      padding: 10px 20px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 500;
    }

    .btn-primary:hover:not(:disabled) {
      background: #5568d3;
    }

    .btn-primary:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .error-message {
      color: #f44336;
      padding: 10px;
      background: #ffebee;
      border-radius: 4px;
      margin-top: 10px;
    }

    .success-message {
      color: #4CAF50;
      padding: 10px;
      background: #e8f5e9;
      border-radius: 4px;
      margin-top: 10px;
    }

    .payroll-list {
      display: flex;
      flex-direction: column;
      gap: 15px;
    }

    .empty-state {
      text-align: center;
      padding: 40px;
      color: #999;
      background: #f5f5f5;
      border-radius: 4px;
    }

    .payroll-card {
      background: #f9f9f9;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 15px;
    }

    .payroll-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 1px solid #e0e0e0;
    }

    .payroll-period {
      font-weight: 600;
      color: #333;
    }

    .payroll-status {
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .payroll-status.status-paid {
      background: #e8f5e9;
      color: #4CAF50;
    }

    .payroll-status.status-pending {
      background: #fff3e0;
      color: #ff9800;
    }

    .payroll-details {
      margin-bottom: 15px;
    }

    .detail-row {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      font-size: 13px;
    }

    .detail-row.net {
      border-top: 1px solid #e0e0e0;
      padding-top: 10px;
      font-weight: 600;
      color: #4CAF50;
    }

    .payroll-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .btn-small {
      padding: 6px 12px;
      border: none;
      border-radius: 4px;
      font-size: 12px;
      cursor: pointer;
    }

    .btn-success {
      background: #4CAF50;
      color: white;
    }

    .btn-info {
      background: #2196F3;
      color: white;
    }

    .btn-download {
      background: #607D8B;
      color: white;
    }

    .payment-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .payment-record {
      background: #f9f9f9;
      padding: 12px;
      border-radius: 6px;
      border-left: 4px solid #2196F3;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 15px;
      flex-wrap: wrap;
    }

    .payment-date {
      font-weight: 500;
      color: #333;
      min-width: 80px;
    }

    .payment-amount {
      font-weight: 600;
      color: #4CAF50;
      font-size: 16px;
    }

    .payment-method {
      color: #666;
      font-size: 13px;
    }

    .payment-status {
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 500;
    }

    .payment-status.status-completed {
      background: #e8f5e9;
      color: #4CAF50;
    }

    .payment-status.status-pending {
      background: #fff3e0;
      color: #ff9800;
    }

    .payment-notes {
      width: 100%;
      color: #999;
      font-size: 12px;
    }
  `]
})
export class WorkerPayrollManagerComponent implements OnInit {
  @Input() selectedWorker: FarmWorker | null = null;
  @Input() farmId: string = '';
  @Input() canViewPayroll = true;

  private fb = inject(FormBuilder);
  private workerService = inject(WorkerManagementService);

  payrollForm!: FormGroup;
  payrollHistory: WorkerPayroll[] = [];
  paymentRecords: any[] = [];

  isLoading = false;
  error: string | null = null;
  success = false;

  // Calculated values
  totalEarned = 0;
  totalPaid = 0;
  outstandingBalance = 0;

  baseSalary = 0;
  bonus = 0;
  allowance = 0;
  taxDeduction = 0;
  insuranceDeduction = 0;
  otherDeduction = 0;

  get grossPay(): number {
    return this.baseSalary + this.bonus + this.allowance;
  }

  get netPay(): number {
    return this.grossPay - this.taxDeduction - this.insuranceDeduction - this.otherDeduction;
  }

  ngOnInit(): void {
    this.initializeForm();
    this.loadPayrollData();
    this.subscribeToFormChanges();
  }

  private initializeForm(): void {
    this.payrollForm = this.fb.group({
      payroll_month: ['', [Validators.required]],
      base_salary: [this.selectedWorker?.salary_amount || 0, [Validators.required]],
      bonus: [0],
      allowance: [0],
      tax_deduction: [0],
      insurance_deduction: [0],
      other_deduction: [0],
      notes: [''],
    });
  }

  private subscribeToFormChanges(): void {
    this.payrollForm.valueChanges.subscribe(values => {
      this.baseSalary = values.base_salary || 0;
      this.bonus = values.bonus || 0;
      this.allowance = values.allowance || 0;
      this.taxDeduction = values.tax_deduction || 0;
      this.insuranceDeduction = values.insurance_deduction || 0;
      this.otherDeduction = values.other_deduction || 0;
    });
  }

  private loadPayrollData(): void {
    if (!this.selectedWorker) return;

    this.workerService.getPayrollHistory(this.selectedWorker.id)
      .then(history => {
        this.payrollHistory = history;
        this.calculateTotals();
      })
      .catch(err => {
        this.error = 'Failed to load payroll: ' + err.message;
      });
  }

  private calculateTotals(): void {
    this.totalEarned = this.payrollHistory.reduce((sum, p) => sum + (p.gross_salary || 0), 0);
    this.totalPaid = this.payrollHistory.filter(p => p.paid).reduce((sum, p) => sum + (p.net_salary || 0), 0);
    this.outstandingBalance = this.totalEarned - this.totalPaid;
  }

  createPayroll(): void {
    if (!this.selectedWorker || !this.payrollForm.valid) return;

    this.isLoading = true;
    this.success = false;
    this.error = null;

    const formValue = this.payrollForm.value;
    const payroll: Omit<WorkerPayroll, 'id' | 'created_at' | 'updated_at'> = {
      farm_id: this.farmId,
      worker_id: this.selectedWorker.id,
      payroll_period_start: formValue.payroll_month,
      payroll_period_end: formValue.payroll_month,
      hours_worked: formValue.hours_worked || 0,
      hourly_rate: this.selectedWorker.hourly_rate || 0,
      base_salary: formValue.base_salary,
      allowances: (formValue.bonus || 0) + (formValue.allowance || 0),
      deductions: (formValue.tax_deduction || 0) + (formValue.insurance_deduction || 0) + (formValue.other_deduction || 0),
      overtime_hours: 0,
      overtime_rate: 0,
      gross_salary: this.grossPay,
      gross_pay: this.grossPay,
      tax: formValue.tax_deduction || 0,
      net_salary: this.netPay,
      net_pay: this.netPay,
      paid: false,
      status: 'pending',
    };

    this.workerService.createPayroll(this.farmId, payroll as any)
      .then(() => {
        this.success = true;
        this.payrollForm.reset();
        this.loadPayrollData();
        setTimeout(() => this.success = false, 3000);
        this.isLoading = false;
      })
      .catch(err => {
        this.error = err.message;
        this.isLoading = false;
      });
  }

  markAsPaid(payroll: WorkerPayroll): void {
    this.isLoading = true;
    this.workerService.markPayrollAsPaid(payroll.id, new Date().toISOString())
      .then(() => {
        this.loadPayrollData();
        this.isLoading = false;
      })
      .catch(err => {
        this.error = err.message;
        this.isLoading = false;
      });
  }

  viewPayslip(payroll: WorkerPayroll): void {
    console.log('Viewing payslip for:', payroll);
    // Implementation for viewing payslip
  }

  downloadPayslip(payroll: WorkerPayroll): void {
    console.log('Downloading payslip for:', payroll);
    // Implementation for downloading payslip
  }

  calculateTotalDeductions(payroll: WorkerPayroll): number {
    return payroll.deductions || 0;
  }

  capitalize(str: string): string {
    return str.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  }
}
