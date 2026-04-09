import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LenderService } from '../../services/lender';
import { Subject, combineLatest } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-lender-wallet',
  imports: [CommonModule, FormsModule],
  templateUrl: './lender-wallet.html',
  styleUrl: './lender-wallet.scss',
})
export class LenderWalletComponent implements OnInit, OnDestroy {
  private lenderService = inject(LenderService);
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
    loanId: '',
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
      this.lenderService.getWalletBalance(),
      this.lenderService.getWalletTransactions(),
    ])
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: ([balance, transactions]) => {
          this.walletBalance = balance.balance || 0;
          this.currency = balance.currency || 'USD';
          this.transactions = transactions.slice(0, 15);
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load wallet data';
          this.loading = false;
        }
      });
  }

  submitTransfer() {
    if (this.transferForm.amount <= 0 || !this.transferForm.loanId) {
      this.error = 'Please enter valid amount and loan ID';
      return;
    }

    if (this.transferForm.amount > this.walletBalance) {
      this.error = 'Insufficient balance';
      return;
    }

    this.lenderService.transferLoanProceeds(this.transferForm.loanId, this.transferForm.amount, 'recipient')
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.successMessage = `Transferred ${this.transferForm.amount} for loan ${this.transferForm.loanId}`;
          this.showTransferForm = false;
          this.transferForm = { amount: 0, loanId: '', description: '' };
          this.loadWalletData();
        },
        error: (err) => {
          this.error = 'Transfer failed';
        }
      });
  }

  cancelTransfer() {
    this.showTransferForm = false;
    this.transferForm = { amount: 0, loanId: '', description: '' };
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
