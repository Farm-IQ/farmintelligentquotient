import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CooperativeService } from '../../services/cooperative';
import { Subject, combineLatest } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-cooperative-wallet',
  imports: [CommonModule, FormsModule],
  templateUrl: './cooperative-wallet.html',
  styleUrl: './cooperative-wallet.scss',
})
export class CooperativeWalletComponent implements OnInit, OnDestroy {
  private cooperativeService = inject(CooperativeService);
  private destroy$ = new Subject<void>();

  walletBalance = 0;
  currency = 'USD';
  transactions: any[] = [];
  loading = false;
  error: string | null = null;
  successMessage: string | null = null;
  showTransferForm = false;

  transferForm = {
    amount: 0,
    recipientCoop: '',
    description: '',
  };

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
      this.cooperativeService.getGroupWalletBalance(),
      this.cooperativeService.getGroupTransactions(),
    ])
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: ([balance, transactions]) => {
          this.walletBalance = balance.balance || 0;
          this.currency = balance.currency || 'USD';
          this.transactions = transactions.slice(0, 10);
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load wallet data';
          this.loading = false;
        }
      });
  }

  submitTransfer() {
    if (this.transferForm.amount <= 0 || !this.transferForm.recipientCoop) {
      this.error = 'Please enter valid amount and recipient';
      return;
    }

    if (this.transferForm.amount > this.walletBalance) {
      this.error = 'Insufficient balance';
      return;
    }

    // Convert transfer form to the correct format for distributeFunds
    const distributionData: Record<string, number> = {
      [this.transferForm.recipientCoop]: this.transferForm.amount,
    };

    this.cooperativeService.distributeFunds(distributionData)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.successMessage = `Transferred ${this.transferForm.amount} to ${this.transferForm.recipientCoop}`;
          this.showTransferForm = false;
          this.transferForm = { amount: 0, recipientCoop: '', description: '' };
          this.loadWalletData();
        },
        error: (err) => {
          this.error = 'Transfer failed';
        }
      });
  }

  cancelTransfer() {
    this.showTransferForm = false;
    this.transferForm = { amount: 0, recipientCoop: '', description: '' };
    this.error = null;
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: this.currency,
    }).format(value);
  }

  getTransactionClass(type: string): string {
    return type === 'credit' ? 'credit' : 'debit';
  }
}
