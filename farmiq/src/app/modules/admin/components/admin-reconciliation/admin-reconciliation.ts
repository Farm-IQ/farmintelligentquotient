import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AdminService } from '../../services/admin';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-admin-reconciliation',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './admin-reconciliation.html',
  styleUrl: './admin-reconciliation.scss',
})
export class AdminReconciliationComponent implements OnInit, OnDestroy {
  private adminService = inject(AdminService);
  private destroy$ = new Subject<void>();

  reconciliationStatus: any = {
    status: 'idle',
    lastRun: new Date(),
    discrepancies: 0,
    resolvedDiscrepancies: 0,
    pendingResolution: 0,
    accuracy: 0,
    nextScheduledRun: new Date()
  };

  reconciliationHistory: any[] = [];
  currentDiscrepancies: any[] = [];
  loading = false;
  reconciling = false;
  error = '';
  successMessage = '';

  ngOnInit() {
    this.loadReconciliationStatus();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadReconciliationStatus() {
    this.loading = true;
    this.adminService.getReconciliationReport()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (report) => {
          this.reconciliationStatus = report;
          this.getReconciliationHistory();
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load reconciliation status';
          this.loading = false;
        }
      });
  }

  runReconciliation() {
    this.reconciling = true;
    this.adminService.runReconciliation()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (result) => {
          this.successMessage = 'Reconciliation completed';
          this.loadReconciliationStatus();
          this.reconciling = false;
        },
        error: (err) => {
          this.error = 'Reconciliation failed';
          this.reconciling = false;
        }
      });
  }

  getReconciliationHistory() {
    this.adminService.getReconciliationHistory()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (history) => {
          this.reconciliationHistory = history;
        },
        error: (err) => this.error = 'Failed to load history'
      });
  }

  getStatusColor(status: string): string {
    if (status === 'completed' || status === 'resolved') return '#4CAF50';
    if (status === 'pending' || status === 'running') return '#FFC107';
    return '#f44336';
  }

  getAccuracyPercentage(): number {
    return this.reconciliationStatus.accuracy * 100;
  }
}
