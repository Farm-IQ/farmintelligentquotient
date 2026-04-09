import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgentService } from '../../services/agent';
import { Subject, combineLatest } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-agent-wallet',
  imports: [CommonModule, FormsModule],
  templateUrl: './agent-wallet.html',
  styleUrl: './agent-wallet.scss',
})
export class AgentWalletComponent implements OnInit, OnDestroy {
  private agentService = inject(AgentService);
  private destroy$ = new Subject<void>();

  walletBalance = 0;
  currency = 'USD';
  commissionEarned = 0;
  commissionPending = 0;
  transactions: any[] = [];
  commissionHistory: any[] = [];
  loading = false;
  error: string | null = null;
  successMessage: string | null = null;

  ngOnInit() {
    this.loadWalletData();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadWalletData() {
    this.loading = true;
    this.error = null;

    combineLatest([
      this.agentService.getWalletBalance(),
      this.agentService.getCommissionHistory(),
      this.agentService.getWalletTransactions(),
    ])
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: ([balance, commissions, txns]) => {
          this.walletBalance = balance.balance || 0;
          this.currency = balance.currency || 'USD';
          this.commissionHistory = commissions.slice(0, 10);
          this.transactions = txns.slice(0, 10);
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load wallet data';
          this.loading = false;
        }
      });
  }

  withdrawCommission(amount: number, bankAccount: string) {
    if (amount <= 0 || amount > this.walletBalance) {
      this.error = 'Invalid withdrawal amount';
      return;
    }

    if (!bankAccount) {
      this.error = 'Bank account required';
      return;
    }

    this.agentService.withdrawCommission(amount, bankAccount)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.successMessage = `Withdrawal of ${this.formatCurrency(amount)} initiated`;
          this.loadWalletData();
        },
        error: (err) => {
          this.error = 'Withdrawal failed';
        }
      });
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: this.currency,
    }).format(value);
  }

  getCommissionStatus(status: string): string {
    const colors: { [key: string]: string } = {
      'earned': '#4CAF50',
      'pending': '#FFC107',
      'paid': '#2196F3',
    };
    return colors[status.toLowerCase()] || '#999';
  }
}
