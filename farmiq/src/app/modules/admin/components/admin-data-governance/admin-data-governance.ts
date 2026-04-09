import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AdminService } from '../../services/admin';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-admin-data-governance',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './admin-data-governance.html',
  styleUrl: './admin-data-governance.scss',
})
export class AdminDataGovernanceComponent implements OnInit, OnDestroy {
  private adminService = inject(AdminService);
  private destroy$ = new Subject<void>();

  dataGovernance: any = {
    dataIntegrity: 0,
    complianceStatus: '',
    encryptionStatus: '',
    backupStatus: '',
    dataRetentionDays: 0,
    lastAudit: new Date()
  };

  complianceMetrics: any[] = [];
  auditHistory: any[] = [];
  loading = false;
  error = '';
  successMessage = '';

  ngOnInit() {
    this.loadDataGovernance();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadDataGovernance() {
    this.loading = true;
    this.adminService.getDataGovernance()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.dataGovernance = data;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load data governance';
          this.loading = false;
        }
      });
  }

  runComplianceAudit() {
    this.loading = true;
    this.adminService.runComplianceAudit()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (result) => {
          this.successMessage = 'Compliance audit completed successfully';
          this.loadDataGovernance();
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Audit failed';
          this.loading = false;
        }
      });
  }

  getAuditHistory() {
    this.adminService.getAuditHistory()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (history) => {
          this.auditHistory = history;
        },
        error: (err) => this.error = 'Failed to load audit history'
      });
  }

  getStatusColor(status: string): string {
    if (status === 'compliant' || status === 'active') return '#4CAF50';
    if (status === 'warning') return '#FFC107';
    return '#f44336';
  }

  getIntegrityPercentage(): number {
    return this.dataGovernance.dataIntegrity || 0;
  }
}
