import { Component, Inject, OnInit, OnDestroy, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { CheckoutService } from '../../services/core/checkout.service';
import { SupabaseService } from '../../services/core/supabase.service';

export interface CheckoutData {
  initialTokens?: number;
}

@Component({
  selector: 'app-checkout-modal',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule
  ],
  templateUrl: './checkout-modal.component.html',
  styleUrls: ['./checkout-modal.component.scss']
})
export class CheckoutModalComponent implements OnInit, OnDestroy {
  checkoutForm!: FormGroup;
  
  // Token packages
  tokenPackages = [10, 30, 50, 100, 500, 1000];
  
  // Pricing: 10 KSH per token
  pricePerToken = 10;
  
  // UI state
  selectedPackage: number | null = null;
  customAmount: number | null = null;
  totalPrice: number = 0;
  isLoading = false;
  isProcessing = false;
  
  // User info
  farmiqId: string | null = null;
  phoneNumber: string = '';
  
  // Payment states
  paymentStep: 'selection' | 'payment' = 'selection';
  paymentMessage: string = '';
  paymentError: string = '';

  private destroy$ = new Subject<void>();

  @Input() initialTokens?: number;
  @Input() initialPrice?: number;
  @Output() closeModal = new EventEmitter<void>();
  @Output() paymentSuccess = new EventEmitter<any>();

  constructor(
    private fb: FormBuilder,
    private checkoutService: CheckoutService,
    private supabaseService: SupabaseService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.initializeForm();
    this.checkUserAuthentication();
    
    // Set initial tokens if provided
    if (this.initialTokens) {
      this.selectCustomAmount(this.initialTokens);
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Initialize the checkout form
   */
  private initializeForm(): void {
    this.checkoutForm = this.fb.group({
      phoneNumber: ['', [Validators.required, Validators.pattern(/^(\+254|0)[0-9]{9}$/)]],
      tokens: [null, [Validators.required, Validators.min(1), Validators.max(100000)]],
      paymentMethod: ['mpesa']
    });
  }

  /**
   * Check if user is authenticated and has FarmIQ ID
   */
  private checkUserAuthentication(): void {
    this.isLoading = true;
    
    // Get current user from Supabase service signals
    const user = this.supabaseService.userSignal$();
    
    if (!user) {
      // No user, redirect to login
      this.paymentError = 'Please log in to purchase tokens.';
      this.router.navigate(['/login']);
      return;
    }
    
    // Get FarmIQ ID from user metadata or user properties using bracket notation
    this.farmiqId = user.user_metadata?.['farmiq_id'] || null;
    
    if (!this.farmiqId) {
      // User logged in but no FarmIQ ID
      this.paymentError = 'Your FarmIQ ID could not be found. Please complete your profile setup.';
      this.isLoading = false;
      return;
    }
    
    // Pre-fill phone number if available using bracket notation
    if (user.user_metadata?.['phone_number']) {
      this.phoneNumber = user.user_metadata['phone_number'];
      this.checkoutForm.patchValue({ phoneNumber: user.user_metadata['phone_number'] });
    }
    
    this.isLoading = false;
  }

  /**
   * Select a token package
   */
  selectPackage(amount: number): void {
    this.selectedPackage = amount;
    this.customAmount = null;
    this.checkoutForm.patchValue({ tokens: amount });
    this.updateTotalPrice();
  }

  /**
   * Select custom token amount
   */
  selectCustomAmount(amount: number): void {
    if (amount > 0 && amount <= 100000) {
      this.customAmount = amount;
      this.selectedPackage = null;
      this.checkoutForm.patchValue({ tokens: amount });
      this.updateTotalPrice();
    }
  }

  /**
   * Handle custom amount input change
   */
  onCustomAmountChange(value: number): void {
    if (value > 0 && value <= 100000) {
      this.selectCustomAmount(value);
    }
  }

  /**
   * Update total price based on token count
   */
  private updateTotalPrice(): void {
    const tokens = this.checkoutForm.get('tokens')?.value;
    this.totalPrice = tokens ? tokens * this.pricePerToken : 0;
  }

  /**
   * Get the current token selection
   */
  getSelectedTokens(): number {
    return this.checkoutForm.get('tokens')?.value || 0;
  }

  /**
   * Check if a package is selected
   */
  isPackageSelected(amount: number): boolean {
    return this.selectedPackage === amount;
  }

  /**
   * Proceed to payment
   */
  proceedToPayment(): void {
    if (!this.checkoutForm.valid) {
      this.paymentError = 'Please fill in all required fields correctly.';
      return;
    }

    if (!this.farmiqId) {
      this.paymentError = 'Your FarmIQ ID is required to complete the transaction.';
      return;
    }

    this.paymentStep = 'payment';
    this.paymentError = '';
    this.paymentMessage = '';
  }

  /**
   * Go back to selection
   */
  backToSelection(): void {
    this.paymentStep = 'selection';
    this.paymentError = '';
    this.paymentMessage = '';
  }

  /**
   * Initiate M-Pesa payment
   */
  initiateMpesaPayment(): void {
    if (!this.checkoutForm.valid || !this.farmiqId) {
      this.paymentError = 'Please fill in all required fields.';
      return;
    }

    this.isProcessing = true;
    this.paymentError = '';
    this.paymentMessage = 'Initiating M-Pesa payment...';

    const tokens = this.checkoutForm.get('tokens')?.value;
    const phoneNumber = this.checkoutForm.get('phoneNumber')?.value;
    const amount = this.totalPrice;

    const paymentRequest = {
      farmiqId: this.farmiqId,
      phoneNumber: phoneNumber,
      tokens: tokens,
      amount: amount,
      description: `FarmIQ Token Purchase: ${tokens} tokens`
    };

    console.log('Initiating M-Pesa payment:', paymentRequest);

    this.checkoutService.initiateMpesaPayment(paymentRequest)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response: any) => {
          console.log('M-Pesa payment response:', response);
          
          this.paymentMessage = 'M-Pesa request sent! Check your phone for the payment prompt on ' + 
                               this.checkoutForm.get('phoneNumber')?.value;
          this.isProcessing = false;
          
          // Get the transaction ID - backend may return different field names
          const transactionId = response.checkout_request_id || response.transactionId || response.id;
          
          if (!transactionId) {
            this.paymentError = 'Payment initiated but could not retrieve transaction ID. Please try again.';
            return;
          }
          
          // Wait for payment confirmation (usually 30-60 seconds)
          // Start polling after 3 seconds to give user time to see the prompt
          setTimeout(() => {
            this.startPaymentPolling(transactionId);
          }, 3000);
        },
        error: (error: any) => {
          this.isProcessing = false;
          console.error('M-Pesa initiation error:', error);
          
          const errorMessage = error?.message || 
                              error?.error?.detail || 
                              error?.error?.message || 
                              'Failed to initiate M-Pesa payment. Please try again.';
          this.paymentError = errorMessage;
        }
      });
  }

  /**
   * Start polling for payment status
   */
  private startPaymentPolling(transactionId: string, attemptCount: number = 0, maxAttempts: number = 20): void {
    if (attemptCount >= maxAttempts) {
      this.paymentError = 'Payment verification timed out. Please check your M-Pesa transaction status.';
      return;
    }

    this.checkPaymentStatus(transactionId, attemptCount + 1, maxAttempts);
  }

  /**
   * Check payment status
   */
  private checkPaymentStatus(
    transactionId: string, 
    attemptCount: number = 1, 
    maxAttempts: number = 20
  ): void {
    this.checkoutService.checkPaymentStatus(transactionId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response: any) => {
          console.log('Payment status response:', response);
          
          if (response.status === 'success' || response.result_code === '0') {
            this.paymentMessage = `✓ Payment successful! ${response.tokens || this.getSelectedTokens()} tokens have been added to your account.`;
            
            // Emit success event after 2 seconds
            setTimeout(() => {
              this.paymentSuccess.emit({
                success: true,
                tokens: response.tokens || this.getSelectedTokens(),
                transactionId: transactionId
              });
            }, 2000);
          } else if (response.status === 'pending' || response.result_code === '1032') {
            // Still waiting for user to complete M-Pesa prompt
            this.paymentMessage = `Payment is being processed... (Attempt ${attemptCount}/${maxAttempts})`;
            
            // Check again in a few seconds, but with exponential backoff
            const delayMs = Math.min(3000 + (attemptCount * 500), 10000);
            
            setTimeout(() => {
              this.startPaymentPolling(transactionId, attemptCount, maxAttempts);
            }, delayMs);
          } else {
            // Payment failed
            const failureReason = response.message || response.error_message || 'Payment was not completed.';
            this.paymentError = `Payment failed: ${failureReason}`;
            this.paymentMessage = '';
          }
        },
        error: (error: any) => {
          console.error('Payment status check error:', error);
          
          // If it's just a network error, retry
          if (attemptCount < maxAttempts) {
            this.paymentMessage = `Checking payment status... (Attempt ${attemptCount}/${maxAttempts})`;
            
            setTimeout(() => {
              this.startPaymentPolling(transactionId, attemptCount, maxAttempts);
            }, 3000);
          } else {
            this.paymentError = error?.message || 'Failed to verify payment status. Please check your M-Pesa message.';
            this.paymentMessage = '';
          }
        }
      });
  }

  /**
   * Cancel and close the modal
   */
  cancel(): void {
    this.closeModal.emit();
  }

  /**
   * Format currency for display
   */
  formatCurrency(amount: number): string {
    return `${amount.toLocaleString('en-KE')} KSH`;
  }

  /**
   * Check if form is valid for submission
   */
  canProceed(): boolean {
    return this.checkoutForm.valid && this.getSelectedTokens() > 0 && !!this.farmiqId;
  }
}
