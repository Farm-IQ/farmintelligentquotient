/**
 * Token Bridge Modal Component
 * Shows when user connects Web3 wallet (HashPack/MetaMask)
 * Allows user to bridge M-Pesa purchased tokens to Hedera blockchain
 */

import { Component, OnInit, OnDestroy, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { TokenBridgeService, BridgeResponse } from '../../services/web3/token-bridge.service';
import { MpesaPaymentService, SupabaseBalance } from '../../services/web3/mpesa-payment.service';
import { Web3WalletService, WalletAccount } from '../../services/web3/web3-wallet.service';
import { SupabaseService } from '../../services/core/supabase.service';

@Component({
  selector: 'app-token-bridge-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './token-bridge-modal.html',
  styleUrls: ['./token-bridge-modal.scss']
})
export class TokenBridgeModalComponent implements OnInit, OnDestroy {
  @Input() connectedAccount: WalletAccount | null = null;
  @Input() supabaseBalance: SupabaseBalance | null = null;
  @Output() bridgeComplete = new EventEmitter<BridgeResponse>();
  @Output() closeModal = new EventEmitter<void>();

  bridgeForm!: FormGroup;
  bridgeStep: 'confirmation' | 'bridging' | 'success' | 'error' = 'confirmation';
  bridgeFee: number = 0;
  bridgeError: string = '';
  bridgeSuccess: boolean = false;

  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    public bridgeService: TokenBridgeService,
    public mpesaService: MpesaPaymentService,
    public web3Service: Web3WalletService,
    public supabaseService: SupabaseService
  ) {}

  ngOnInit(): void {
    this.initializeBridgeForm();
    this.calculateBridgeFee();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initializeBridgeForm(): void {
    const availableBalance = this.supabaseBalance?.balance || 0;

    this.bridgeForm = this.fb.group({
      amount: [availableBalance, [
        Validators.required,
        Validators.min(1),
        Validators.max(availableBalance)
      ]],
      agreeToTerms: [false, Validators.requiredTrue]
    });
  }

  private async calculateBridgeFee(): Promise<void> {
    const amount = this.bridgeForm?.get('amount')?.value || 0;
    this.bridgeFee = await this.bridgeService.getBridgeFee(amount);
  }

  get finalAmount(): number {
    const amount = this.bridgeForm?.get('amount')?.value || 0;
    return amount - this.bridgeFee;
  }

  get availableBalance(): number {
    return this.supabaseBalance?.balance || 0;
  }

  /**
   * Initiate token bridge
   * Transfers tokens from Supabase to Hedera wallet
   */
  async bridgeTokens(): Promise<void> {
    if (!this.bridgeForm.valid || !this.connectedAccount || !this.supabaseBalance) {
      return;
    }

    if (this.connectedAccount.provider === 'unknown') {
      this.bridgeError = 'Unknown wallet provider. Please connect a supported wallet (HashPack or MetaMask).';
      this.bridgeStep = 'error';
      return;
    }

    this.bridgeStep = 'bridging';
    this.bridgeError = '';

    const farmiqId = this.supabaseService.farmiqIdSignal$();
    if (!farmiqId) {
      this.bridgeError = 'Unable to identify user. Please refresh and try again.';
      this.bridgeStep = 'error';
      return;
    }

    const bridgeRequest = {
      farmiqId,
      hederaAccountId: this.connectedAccount.address,
      amount: this.bridgeForm.get('amount')?.value,
      provider: this.connectedAccount.provider
    };

    this.bridgeService
      .bridgeTokensToHedera(bridgeRequest)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response: BridgeResponse) => {
          if (response.success) {
            this.bridgeSuccess = true;
            this.bridgeStep = 'success';
            this.bridgeComplete.emit(response);
            
            // Refresh Web3 balance after bridge
            setTimeout(() => {
              this.web3Service.loadTokenBalance();
            }, 2000);
          } else {
            this.bridgeError = response.message || 'Bridge failed. Please try again.';
            this.bridgeStep = 'error';
          }
        },
        error: (error: any) => {
          this.bridgeError = error.message || 'An error occurred during bridging. Please try again.';
          this.bridgeStep = 'error';
          console.error('Bridge error:', error);
        }
      });
  }

  onAmountChange(): void {
    this.calculateBridgeFee();
  }

  dismissModal(): void {
    this.closeModal.emit();
  }
}
