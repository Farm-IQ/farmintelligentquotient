import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { FarmerService } from '../../services/farmer.service';
import { Web3WalletService, WalletAccount, TokenBalance, Transaction as Web3Transaction } from '../../../../services/web3/web3-wallet.service';
import { TokenBridgeService } from '../../../../services/web3/token-bridge.service';
import { MpesaPaymentService, SupabaseBalance } from '../../../../services/web3/mpesa-payment.service';
import { TokenBridgeModalComponent } from '../../../../components/token-bridge-modal/token-bridge-modal.component';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface WalletBalance {
  available_balance: number;
}

interface Transaction {
  description: string;
  amount: number;
  type: 'sent' | 'received' | 'credit' | 'debit';
  date: string;
}

@Component({
  selector: 'app-farmer-wallet',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, IonicModule, TokenBridgeModalComponent],
  templateUrl: './farmer-wallet.html',
  styleUrls: ['./farmer-wallet.scss']
})
export class FarmerWalletComponent implements OnInit, OnDestroy {
  // Traditional Wallet Properties
  walletBalance: WalletBalance | null = null;
  transactions: Transaction[] = [];
  supabaseBalance: SupabaseBalance | null = null;
  loading = true;
  refreshing = false;
  error: string | null = null;
  activeTab = 'all';
  currency = 'USD';
  
  // Web3 Wallet Properties
  connectedAccount: WalletAccount | null = null;
  fqTokenBalance: TokenBalance | null = null;
  web3Transactions: Web3Transaction[] = [];
  walletTab: 'traditional' | 'web3' = 'traditional';
  complianceInfo: any = null;
  showComplianceWarning = true;
  isConnecting = false;
  showTransferForm = false;
  transferLoading = false;

  // Bridge Modal Properties
  showBridgeModal = false;
  isBridgeEligible = false;
  
  // Forms
  transferForm = {
    amount: 0,
    recipient: '',
    description: ''
  };
  web3TransferForm: FormGroup;
  
  private destroy$ = new Subject<void>();

  constructor(
    private farmerService: FarmerService,
    private web3Service: Web3WalletService,
    private bridgeService: TokenBridgeService,
    private mpesaService: MpesaPaymentService,
    private formBuilder: FormBuilder
  ) {
    this.web3TransferForm = this.formBuilder.group({
      recipientAddress: ['', Validators.required],
      amount: ['', [Validators.required, Validators.min(0.00000001)]]
    });
  }

  ngOnInit(): void {
    this.loadWalletData();
    this.loadSupabaseBalance();
    this.setupWeb3Listeners();
    this.complianceInfo = this.web3Service.getComplianceInfo();
  }

  loadWallet(): void {
    this.refreshing = true;
    this.loadWalletData();
    setTimeout(() => {
      this.refreshing = false;
    }, 1000);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadWalletData(): void {
    this.loading = true;
    this.error = null;

    this.farmerService.getWalletBalance()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data: any) => {
          this.walletBalance = data;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load wallet';
          this.loading = false;
          console.error('Wallet load error:', err);
        }
      });

    this.farmerService.getTransactionHistory()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data: any) => {
          this.transactions = data;
        },
        error: (err: any) => {
          console.error('Error loading transactions:', err);
        }
      });
  }

  filterTransactions(): Transaction[] {
    if (this.activeTab === 'all') return this.transactions;
    return this.transactions.filter(t => t.type === this.activeTab);
  }

  submitTransfer(): void {
    if (!this.transferForm.amount || !this.transferForm.recipient) {
      this.error = 'Please fill in all required fields';
      return;
    }

    this.transferLoading = true;
    this.error = null;

    this.farmerService.transferFunds(this.transferForm.amount, this.transferForm.recipient)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.transferLoading = false;
          this.showTransferForm = false;
          this.transferForm = { amount: 0, recipient: '', description: '' };
          this.loadWalletData();
        },
        error: (err) => {
          this.error = 'Transfer failed. Please try again.';
          this.transferLoading = false;
        }
      });
  }

  cancelTransfer(): void {
    this.showTransferForm = false;
    this.transferForm = { amount: 0, recipient: '', description: '' };
    this.web3TransferForm.reset();
  }
  setupWeb3Listeners(): void {
    this.web3Service.getAccount$()
      .pipe(takeUntil(this.destroy$))
      .subscribe(account => {
        this.connectedAccount = account;
        
        // Show bridge modal when wallet connects for first time
        if (account && this.isBridgeEligible && !this.showBridgeModal) {
          this.showBridgeModal = true;
        }
      });

    this.web3Service.getTokenBalance$()
      .pipe(takeUntil(this.destroy$))
      .subscribe(balance => {
        this.fqTokenBalance = balance;
      });

    this.web3Service.getTransactions$()
      .pipe(takeUntil(this.destroy$))
      .subscribe(txs => {
        this.web3Transactions = txs;
      });
  }

  async connectHashPack(): Promise<void> {
    try {
      this.isConnecting = true;
      await this.web3Service.connectHashPack();
      this.walletTab = 'web3';
    } catch (err: any) {
      this.error = err.message || 'Failed to connect to HashPack';
    } finally {
      this.isConnecting = false;
    }
  }

  async connectMetaMask(): Promise<void> {
    try {
      this.isConnecting = true;
      await this.web3Service.connectMetaMask();
      this.walletTab = 'web3';
    } catch (err: any) {
      this.error = err.message || 'Failed to connect to MetaMask';
    } finally {
      this.isConnecting = false;
    }
  }

  async disconnectWeb3Wallet(): Promise<void> {
    try {
      await this.web3Service.disconnect();
      this.connectedAccount = null;
      this.fqTokenBalance = null;
      this.web3Transactions = [];
    } catch (err: any) {
      this.error = err.message || 'Failed to disconnect wallet';
    }
  }

  async submitWeb3Transfer(): Promise<void> {
    if (!this.web3TransferForm.valid) {
      this.error = 'Please fill in all required fields';
      return;
    }

    try {
      this.transferLoading = true;
      this.error = null;

      const { recipientAddress, amount } = this.web3TransferForm.value;
      await this.web3Service.transferTokens(recipientAddress, amount);

      this.web3TransferForm.reset();
      this.showTransferForm = false;
      await this.web3Service.loadTransactionHistory();
    } catch (err: any) {
      this.error = err.message || 'Transfer failed';
    } finally {
      this.transferLoading = false;
    }
  }

  dismissComplianceWarning(): void {
    this.showComplianceWarning = false;
  }

  /**
   * Load M-Pesa purchased FIQ balance from Supabase
   */
  loadSupabaseBalance(): void {
    this.mpesaService.loadSupabaseBalance();
    
    this.mpesaService.balance$
      .pipe(takeUntil(this.destroy$))
      .subscribe(balance => {
        this.supabaseBalance = balance;
        
        // Check if user is eligible to bridge (has balance and not yet bridged)
        if (balance && balance.balance > 0) {
          this.isBridgeEligible = true;
        }
      });
  }

  /**
   * Handle successful bridge - refresh balances
   */
  onBridgeSuccess(): void {
    this.showBridgeModal = false;
    
    // Reload balances from both sources
    this.loadSupabaseBalance();
    this.web3Service.loadTokenBalance();
    
    // Show success message
    this.error = null;
    console.log('Bridge completed successfully!');
  }

  /**
   * Close bridge modal
   */
  closeBridgeModal(): void {
    this.showBridgeModal = false;
  }
}
