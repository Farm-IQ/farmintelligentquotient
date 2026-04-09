import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { Web3WalletService, WalletAccount, TokenBalance, Transaction as Web3Transaction } from '../../../../services/web3/web3-wallet.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-worker-wallet',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, IonicModule],
  templateUrl: './worker-wallet.html',
  styleUrl: './worker-wallet.scss'
})
export class WorkerWalletComponent implements OnInit, OnDestroy {
  // Web3 wallet state
  connectedAccount: WalletAccount | null = null;
  fqTokenBalance: TokenBalance | null = null;
  web3Transactions: Web3Transaction[] = [];

  // UI state
  loading = true;
  error: string | null = null;
  isConnecting = false;
  showComplianceWarning = false;

  web3TransferForm!: FormGroup;
  showTransferForm = false;
  transferLoading = false;
  complianceInfo: any = null;

  private destroy$ = new Subject<void>();

  constructor(
    private web3Wallet: Web3WalletService,
    private fb: FormBuilder
  ) {
    this.initializeForms();
  }

  ngOnInit(): void {
    this.loading = false;
    this.setupWeb3Listeners();
  }

  private initializeForms(): void {
    this.web3TransferForm = this.fb.group({
      recipientAddress: ['', [Validators.required]],
      amount: [0, [Validators.required, Validators.min(0.00000001)]]
    });
  }

  private setupWeb3Listeners(): void {
    this.web3Wallet.getAccount$()
      .pipe(takeUntil(this.destroy$))
      .subscribe(account => {
        this.connectedAccount = account;
        if (account) {
          this.loadWeb3Data();
          this.showComplianceWarning = true;
          this.complianceInfo = this.web3Wallet.getComplianceInfo();
        }
      });

    this.web3Wallet.getTokenBalance$()
      .pipe(takeUntil(this.destroy$))
      .subscribe(balance => {
        this.fqTokenBalance = balance;
      });

    this.web3Wallet.getTransactions$()
      .pipe(takeUntil(this.destroy$))
      .subscribe(txs => {
        this.web3Transactions = txs;
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private async loadWeb3Data(): Promise<void> {
    try {
      await this.web3Wallet.loadTokenBalance();
      await this.web3Wallet.loadTransactionHistory();
    } catch (err: any) {
      console.error('Error loading Web3 data:', err);
    }
  }

  async connectHashPack(): Promise<void> {
    this.isConnecting = true;
    this.error = null;

    try {
      await this.web3Wallet.connectHashPack();
    } catch (err: any) {
      this.error = err.message || 'Failed to connect HashPack';
    } finally {
      this.isConnecting = false;
    }
  }

  async connectMetaMask(): Promise<void> {
    this.isConnecting = true;
    this.error = null;

    try {
      await this.web3Wallet.connectMetaMask();
    } catch (err: any) {
      this.error = err.message || 'Failed to connect MetaMask';
    } finally {
      this.isConnecting = false;
    }
  }

  async disconnectWeb3Wallet(): Promise<void> {
    await this.web3Wallet.disconnect();
    this.connectedAccount = null;
    this.fqTokenBalance = null;
    this.web3Transactions = [];
    this.showComplianceWarning = false;
  }

  async submitWeb3Transfer(): Promise<void> {
    if (this.web3TransferForm.invalid) {
      this.error = 'Please fill in all required fields';
      return;
    }

    this.transferLoading = true;
    this.error = null;

    try {
      const { recipientAddress, amount } = this.web3TransferForm.value;
      const txHash = await this.web3Wallet.transferTokens(recipientAddress, amount);

      this.web3TransferForm.reset();
      this.showTransferForm = false;
      await this.loadWeb3Data();
    } catch (err: any) {
      this.error = err.message || 'Transfer failed. Please try again.';
    } finally {
      this.transferLoading = false;
    }
  }

  cancelTransfer(): void {
    this.showTransferForm = false;
    this.web3TransferForm.reset();
  }

  dismissComplianceWarning(): void {
    this.showComplianceWarning = false;
  }
}
