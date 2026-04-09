import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, retry, timeout, map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface PaymentRequest {
  farmiqId: string;
  phoneNumber: string;
  tokens: number;
  amount: number;
  description: string;
}

export interface PaymentResponse {
  success: boolean;
  transactionId: string;
  message?: string;
  checkoutUrl?: string;
}

export interface PaymentStatusResponse {
  status: 'success' | 'pending' | 'failed';
  transactionId: string;
  tokens?: number;
  message?: string;
  timestamp?: string;
}

@Injectable({
  providedIn: 'root'
})
export class CheckoutService {
  // M-Pesa API endpoints - Using backend Daraja API
  private backendUrl = environment.backendUrl;
  private mpesaInitiateUrl = `${this.backendUrl}v1/mpesa/initiate-purchase`;
  private mpesaStatusUrl = `${this.backendUrl}v1/mpesa/status`;
  private mpesaPackagesUrl = `${this.backendUrl}v1/mpesa/packages`;

  constructor(private http: HttpClient) {}
  
  /**
   * Log API configuration for debugging
   */
  private logConfig(): void {
    console.log('CheckoutService - M-Pesa Configuration:', {
      backendUrl: this.backendUrl,
      initiateUrl: this.mpesaInitiateUrl,
      statusUrl: this.mpesaStatusUrl,
      packagesUrl: this.mpesaPackagesUrl
    });
  }

  /**
   * Initiate M-Pesa payment
   * @param paymentRequest - Payment details including FarmIQ ID, phone, tokens amount
   * @returns Observable with transaction ID and checkout details
   * 
   * Backend will:
   * 1. Generate STK Push prompt on user's phone
   * 2. User enters M-Pesa PIN
   * 3. Callback received with payment status
   * 4. Tokens credited to user account
   */
  initiateMpesaPayment(paymentRequest: PaymentRequest): Observable<PaymentResponse> {
    this.logConfig();
    
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    // Transform frontend format to backend format
    const backendPayload = {
      phone_number: this.formatPhoneNumber(paymentRequest.phoneNumber),
      amount: paymentRequest.amount,
      account_reference: paymentRequest.farmiqId,
      transaction_desc: paymentRequest.description || `FarmIQ Token Purchase: ${paymentRequest.tokens} tokens`
    };

    console.log('Initiating M-Pesa payment with payload:', backendPayload);

    return this.http.post<PaymentResponse>(
      this.mpesaInitiateUrl,
      backendPayload,
      { headers }
    ).pipe(
      timeout(30000), // 30 second timeout
      retry(1), // Retry once on failure
      catchError(error => {
        console.error('M-Pesa payment initiation error:', error);
        const errorMessage = error?.error?.detail || 
                           error?.error?.message || 
                           'Failed to initiate M-Pesa payment. Please try again.';
        return throwError(() => new Error(errorMessage));
      })
    );
  }

  /**
   * Check payment status
   * @param transactionId - Checkout request ID returned from initiate payment
   * @returns Observable with payment status (success, pending, or failed)
   * 
   * The backend checks Safaricom's M-Pesa Daraja API for the latest status
   */
  checkPaymentStatus(transactionId: string): Observable<PaymentStatusResponse> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    console.log('Checking payment status for transaction:', transactionId);

    return this.http.get<PaymentStatusResponse>(
      `${this.mpesaStatusUrl}/${transactionId}`,
      { headers }
    ).pipe(
      timeout(15000), // 15 second timeout
      retry(0), // No retry for status checks (to avoid excessive polling)
      catchError(error => {
        console.error('Payment status check error:', error);
        const errorMessage = error?.error?.detail || 
                           error?.error?.message || 
                           'Failed to check payment status.';
        return throwError(() => new Error(errorMessage));
      })
    );
  }

  /**
   * Verify payment after user confirms M-Pesa transaction
   * @param transactionId - Transaction ID to verify
   * @returns Observable with verification result
   */
  verifyPayment(transactionId: string): Observable<PaymentStatusResponse> {
    return this.checkPaymentStatus(transactionId);
  }

  /**
   * Get payment history for a user
   * @param farmiqId - FarmIQ ID of user
   * @returns Observable with payment history
   */
  getPaymentHistory(farmiqId: string): Observable<any[]> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    const historyUrl = `${this.backendUrl}v1/mpesa/history/${farmiqId}`;

    return this.http.get<any>(
      historyUrl,
      { headers }
    ).pipe(
      timeout(15000),
      map(response => response.transactions || response || []),
      catchError(error => {
        console.error('Payment history fetch error:', error);
        return throwError(() => new Error('Failed to fetch payment history.'));
      })
    );
  }

  /**
   * Get available token packages from backend
   * @returns Observable with list of available packages
   * 
   * Backend returns packages like:
   * { packages: [
   *   { name: "Starter", tokens: 100, price: 150 },
   *   { name: "Standard", tokens: 500, price: 750 },
   *   ...
   * ]}
   */
  getTokenPackages(): Observable<any[]> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    return this.http.get<any>(
      this.mpesaPackagesUrl,
      { headers }
    ).pipe(
      timeout(10000),
      map(response => response.packages || response || []),
      catchError(error => {
        console.error('Token packages fetch error:', error);
        // Return default packages if backend fetch fails
        console.log('Using fallback token packages');
        return Promise.resolve([
          { amount: 10, price: 150, name: 'Starter' },
          { amount: 30, price: 300, name: 'Small' },
          { amount: 50, price: 500, name: 'Medium' },
          { amount: 100, price: 1000, name: 'Standard' },
          { amount: 500, price: 5000, name: 'Premium' },
          { amount: 1000, price: 10000, name: 'Enterprise' }
        ]);
      })
    );
  }

  /**
   * Calculate total price for tokens
   * @param tokenCount - Number of tokens
   * @param pricePerToken - Price per token in KSH
   * @returns Total price
   */
  calculateTotalPrice(tokenCount: number, pricePerToken: number = 10): number {
    return tokenCount * pricePerToken;
  }

  /**
   * Format phone number to E.164 format for M-Pesa
   * @param phoneNumber - Phone number in various formats
   * @returns Formatted phone number (e.g., +254712345678)
   */
  formatPhoneNumber(phoneNumber: string): string {
    let formatted = phoneNumber.trim().replace(/\s/g, '');

    // Remove leading 0 if present
    if (formatted.startsWith('0')) {
      formatted = formatted.substring(1);
    }

    // Add country code if not present
    if (!formatted.startsWith('+')) {
      if (!formatted.startsWith('254')) {
        formatted = '254' + formatted;
      }
      formatted = '+' + formatted;
    }

    return formatted;
  }

  /**
   * Validate phone number format
   * @param phoneNumber - Phone number to validate
   * @returns true if valid, false otherwise
   */
  isValidPhoneNumber(phoneNumber: string): boolean {
    const pattern = /^(\+254|0)[0-9]{9}$/;
    return pattern.test(phoneNumber);
  }
}
