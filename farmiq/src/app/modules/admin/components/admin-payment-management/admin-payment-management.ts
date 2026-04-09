import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminService } from '../../services/admin';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-admin-payment-management',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-payment-management.html',
  styleUrl: './admin-payment-management.scss',
})
export class AdminPaymentManagementComponent implements OnInit, OnDestroy {
  private adminService = inject(AdminService);
  private destroy$ = new Subject<void>();

  paymentStatus: any = {
    totalRevenue: 0,
    pendingPayouts: 0,
    completedPayouts: 0,
    failedPayments: 0,
    lastPaymentRun: new Date()
  };

  paymentTransactions: any[] = [];
  selectedPayment: any = null;
  loading = false;
  processing = false;
  error = '';
  successMessage = '';

  filterStatus = 'all';

  ngOnInit() {
    this.loadPaymentStatus();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadPaymentStatus() {
    this.loading = true;
    this.adminService.getPaymentStatus()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (status) => {
          this.paymentStatus = status;
          this.getPaymentTransactions();
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load payment status';
          this.loading = false;
        }
      });
  }

  getPaymentTransactions() {
    this.adminService.getPaymentTransactions()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (transactions) => {
          this.paymentTransactions = transactions;
        },
        error: (err) => this.error = 'Failed to load transactions'
      });
  }

  processPayment(paymentId: string) {
    this.processing = true;
    this.adminService.processPayment({ id: paymentId })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (result) => {
          this.successMessage = 'Payment processed successfully';
          this.loadPaymentStatus();
          this.processing = false;
        },
        error: (err) => {
          this.error = 'Payment processing failed';
          this.processing = false;
        }
      });
  }

  getStatusColor(status: string): string {
    if (status === 'completed') return '#4CAF50';
    if (status === 'pending') return '#FFC107';
    return '#f44336';
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  }
}
