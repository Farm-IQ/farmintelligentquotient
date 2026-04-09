import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AdminService } from '../../services/admin';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-admin-hcs-integration',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './admin-hcs-integration.html',
  styleUrl: './admin-hcs-integration.scss',
})
export class AdminHcsIntegrationComponent implements OnInit, OnDestroy {
  private adminService = inject(AdminService);
  private destroy$ = new Subject<void>();

  hcsIntegration: any = {
    status: 'connected',
    lastSync: new Date(),
    syncFrequency: 'hourly',
    transactionsProcessed: 0,
    transactionsFailed: 0,
    averageConfirmationTime: '45s',
    gasUsage: 0,
    networkStatus: 'mainnet'
  };

  recentTransactions: any[] = [];
  loading = false;
  syncing = false;
  error = '';
  successMessage = '';

  ngOnInit() {
    this.loadHcsIntegration();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadHcsIntegration() {
    this.loading = true;
    this.adminService.getHCSIntegration()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (integration) => {
          this.hcsIntegration = integration;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load HCS integration';
          this.loading = false;
        }
      });
  }

  syncWithHedera() {
    this.syncing = true;
    this.adminService.getHCSIntegration()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (result) => {
          this.successMessage = 'Successfully synced with Hedera';
          this.loadHcsIntegration();
          this.syncing = false;
        },
        error: (err) => {
          this.error = 'Sync failed';
          this.syncing = false;
        }
      });
  }

  verifyTransaction(txHash: string) {
    this.adminService.verifyBlockchainTransaction(txHash)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (result) => {
          this.successMessage = 'Transaction verified';
        },
        error: (err) => this.error = 'Verification failed'
      });
  }

  getStatusColor(status: string): string {
    if (status === 'connected') return '#4CAF50';
    if (status === 'reconnecting') return '#FFC107';
    return '#f44336';
  }
}
