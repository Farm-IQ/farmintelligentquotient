/**
 * M-Pesa Payment Service
 * Handles M-Pesa STK Push payments and balance state management
 * Integrates with Web3 wallet for bridge notifications
 */

import { Injectable, signal } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable, interval, throwError } from 'rxjs';
import { catchError, timeout, switchMap, takeUntil, map, tap } from 'rxjs/operators';
import { Subject } from 'rxjs';
import { environment } from '../../../environments/environment';
import { SupabaseService } from '../core/supabase.service';

export interface MpesaPaymentRequest {
  phone_number: string;
  amount: number; // KES amount
  account_reference: string; // FarmIQ ID
  transaction_desc: string; // Payment description
}

export interface MpesaPaymentResponse {
  merchant_request_id: string;
  checkout_request_id: string;
  response_code: string;
  response_description: string;
  customer_message: string;
}

export interface MpesaPaymentStatus {
  checkout_request_id: string;
  status: 'pending' | 'success' | 'failed' | 'timeout';
  result_code?: string;
  result_desc?: string;
  amount?: number;
  tokens_purchased?: number;
  phone_number?: string;
  timestamp?: string;
}

export interface SupabaseBalance {
  farmiq_id: string;
  balance: number;
  last_updated: string;
  pending_bridge?: number;
}

@Injectable({
  providedIn: 'root'
})
export class MpesaPaymentService {
  private backendUrl = environment.backendUrl;
  private mpesaInitiateUrl = `${this.backendUrl}v1/mpesa/initiate-purchase`;
  private mpesaStatusUrl = `${this.backendUrl}v1/mpesa/status`;
  private mpesaHistoryUrl = `${this.backendUrl}v1/mpesa/history`;
  private balanceUrl = `${this.backendUrl}v1/wallet/balance`;

  // State management with signals
  isProcessing = signal(false);
  paymentError = signal<string | null>(null);
  paymentSuccess = signal(false);
  lastPaymentCheckoutId = signal<string | null>(null);
  currentSupabaseBalance = signal<SupabaseBalance | null>(null);
  isBalanceLoading = signal(false);

  private paymentStatusSubject = new BehaviorSubject<MpesaPaymentStatus | null>(
    null
  );
  paymentStatus$ = this.paymentStatusSubject.asObservable();

  private balanceSubject = new BehaviorSubject<SupabaseBalance | null>(null);
  balance$ = this.balanceSubject.asObservable();

  private statusCheckCancel$ = new Subject<void>();

  constructor(
    private http: HttpClient,
    private supabaseService: SupabaseService
  ) {
    this.logConfiguration();
  }

  private logConfiguration(): void {
    console.log('MpesaPaymentService initialized', {
      backendUrl: this.backendUrl,
      mpesaInitiateUrl: this.mpesaInitiateUrl,
      mpesaStatusUrl: this.mpesaStatusUrl,
      balanceUrl: this.balanceUrl,
      tokenRate: '1 FIQ = 1 KSH'
    });
  }

  /**
   * Initiate M-Pesa STK Push payment
   * M-Pesa prompt will appear on user's phone
   * Returns checkout_request_id for status polling
   */
  initiateMpesaPayment(request: MpesaPaymentRequest): Observable<MpesaPaymentResponse> {
    this.isProcessing.set(true);
    this.paymentError.set(null);
    this.paymentSuccess.set(false);

    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    console.log('Initiating M-Pesa payment:', {
      phone: request.phone_number,
      amount: request.amount,
      farmiqId: request.account_reference
    });

    return this.http
      .post<MpesaPaymentResponse>(this.mpesaInitiateUrl, request, { headers })
      .pipe(
        timeout(30000),
        tap((response) => {
          console.log('M-Pesa payment initiated:', response);
          this.lastPaymentCheckoutId.set(response.checkout_request_id);
          this.isProcessing.set(false);
        }),
        catchError((error) => {
          this.isProcessing.set(false);
          const errorMessage =
            error?.error?.detail ||
            error?.error?.message ||
            'Failed to initiate M-Pesa payment. Please check your phone and internet connection.';

          this.paymentError.set(errorMessage);
          console.error('M-Pesa payment error:', error);
          return throwError(() => new Error(errorMessage));
        })
      );
  }

  /**
   * Poll M-Pesa payment status
   * Checks status every 2 seconds for up to 2 minutes
   * Returns observable that completes when payment succeeds/fails
   */
  pollPaymentStatus(
    checkoutRequestId: string,
    maxAttempts: number = 60
  ): Observable<MpesaPaymentStatus> {
    let attempts = 0;

    return interval(2000).pipe(
      switchMap(() => {
        attempts++;
        console.log(`Polling payment status (attempt ${attempts}/${maxAttempts})`);

        if (attempts > maxAttempts) {
          this.statusCheckCancel$.next();
          return throwError(() => new Error('Payment timeout. Please check M-Pesa on your phone.'));
        }

        return this.checkPaymentStatus(checkoutRequestId);
      }),
      takeUntil(this.statusCheckCancel$),
      tap((status) => {
        this.paymentStatusSubject.next(status);

        if (status.status === 'success') {
          console.log('Payment successful!', status);
          this.paymentSuccess.set(true);
          this.statusCheckCancel$.next(); // Stop polling
          this.loadSupabaseBalance(); // Sync balance
        } else if (status.status === 'failed') {
          console.log('Payment failed:', status);
          this.paymentError.set(status.result_desc || 'Payment failed');
          this.statusCheckCancel$.next(); // Stop polling
        }
      }),
      catchError((error) => {
        this.paymentError.set(error.message || 'Error checking payment status');
        console.error('Status check error:', error);
        return throwError(() => error);
      })
    );
  }

  /**
   * Check single payment status
   */
  private checkPaymentStatus(
    checkoutRequestId: string
  ): Observable<MpesaPaymentStatus> {
    return this.http
      .get<MpesaPaymentStatus>(`${this.mpesaStatusUrl}/${checkoutRequestId}`)
      .pipe(
        timeout(10000),
        catchError((error) => {
          console.error('Error checking status:', error);
          return throwError(() => error);
        })
      );
  }

  /**
   * Load current FIQ balance from Supabase
   * This is the M-Pesa purchased token balance
   */
  loadSupabaseBalance(farmiqId?: string): void {
    this.isBalanceLoading.set(true);

    const storedFarmiqId = this.supabaseService.farmiqIdSignal$();
    const id = farmiqId || storedFarmiqId;

    if (!id) {
      console.warn('No FarmIQ ID available for balance query');
      this.isBalanceLoading.set(false);
      return;
    }

    this.http
      .get<SupabaseBalance>(`${this.balanceUrl}/${id}`)
      .pipe(
        timeout(10000),
        tap((balance) => {
          console.log('Balance loaded:', balance);
          this.currentSupabaseBalance.set(balance);
          this.balanceSubject.next(balance);
        }),
        catchError((error) => {
          console.error('Error loading balance:', error);
          return throwError(() => error);
        })
      )
      .subscribe({
        complete: () => {
          this.isBalanceLoading.set(false);
        },
        error: () => {
          this.isBalanceLoading.set(false);
        }
      });
  }

  /**
   * Get payment history for user
   * Shows all M-Pesa purchases
   */
  getPaymentHistory(farmiqId: string): Observable<MpesaPaymentStatus[]> {
    return this.http
      .get<MpesaPaymentStatus[]>(`${this.mpesaHistoryUrl}/${farmiqId}`)
      .pipe(
        timeout(30000),
        catchError((error) => {
          console.error('Error loading payment history:', error);
          return throwError(() => error);
        })
      );
  }

  /**
   * Cancel payment status polling
   */
  stopStatusPolling(): void {
    this.statusCheckCancel$.next();
    this.isProcessing.set(false);
  }

  /**
   * Clear payment state
   */
  clearPaymentState(): void {
    this.isProcessing.set(false);
    this.paymentError.set(null);
    this.paymentSuccess.set(false);
    this.lastPaymentCheckoutId.set(null);
  }

  /**
   * Format phone number for M-Pesa API
   * Accepts: 254XXXXXXXXX, +254XXXXXXXXX, 0XXXXXXXXX
   * Returns: 254XXXXXXXXX format
   */
  formatPhoneNumber(phoneNumber: string): string {
    let formatted = phoneNumber.replace(/\D/g, ''); // Remove non-digits

    if (formatted.startsWith('254')) {
      return formatted; // Already in correct format
    } else if (formatted.startsWith('0')) {
      return formatted.replace(/^0/, '254'); // Replace leading 0
    } else {
      return '254' + formatted; // Prepend country code
    }
  }

  /**
   * Validate phone number format
   */
  isValidPhoneNumber(phoneNumber: string): boolean {
    const pattern = /^(\+254|254|0)[0-9]{9}$/;
    return pattern.test(phoneNumber);
  }

  /**
   * Calculate FIQ tokens from KES amount
   * Rate: 1 FIQ = 1 KSH
   */
  calculateTokens(kesAmount: number): number {
    return kesAmount * 1; // 1 FIQ per 1 KSH
  }

  /**
   * Calculate KES amount from FIQ tokens
   * Rate: 1 FIQ = 1 KSH
   */
  calculateKES(fiqTokens: number): number {
    return fiqTokens * 1; // 1 KSH per 1 FIQ
  }
}
