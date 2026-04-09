/**
 * Token Bridge Service
 * Handles bridging FIQ tokens between Supabase (traditional) and Hedera (blockchain)
 * 
 * Flow:
 * 1. User purchases tokens via M-Pesa → stored in Supabase
 * 2. User connects Web3 wallet (HashPack/MetaMask)
 * 3. User initiates bridge → tokens minted on Hedera
 * 4. Tokens deducted from Supabase, added to Hedera wallet
 */

import { Injectable, signal } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { catchError, timeout, tap } from 'rxjs/operators';
import { SupabaseService } from '../core/supabase.service';
import { Web3WalletService, WalletAccount } from './web3-wallet.service';
import { environment } from '../../../environments/environment';

export interface BridgeRequest {
  farmiqId: string;
  hederaAccountId: string;
  amount: number; // FIQ amount to bridge
  provider: 'hashpack' | 'metamask';
}

export interface BridgeResponse {
  success: boolean;
  transactionHash: string;
  supabaseAmount: number; // Amount deducted from Supabase
  hederaAmount: number; // Amount minted on Hedera
  message: string;
  timestamp: string;
}

export interface BridgeHistory {
  id: string;
  timestamp: string;
  fromAmount: number;
  toAmount: number;
  status: 'pending' | 'completed' | 'failed';
  hederaTxHash?: string;
  supabaseTxId?: string;
}

@Injectable({
  providedIn: 'root'
})
export class TokenBridgeService {
  private backendUrl = environment.backendUrl;
  private bridgeUrl = `${this.backendUrl}v1/bridge/transfer-tokens`;
  private bridgeStatusUrl = `${this.backendUrl}v1/bridge/status`;
  private bridgeHistoryUrl = `${this.backendUrl}v1/bridge/history`;

  // State management
  isBridging = signal(false);
  bridgeError = signal<string | null>(null);
  bridgeSuccess = signal(false);
  lastBridgeTransaction = signal<BridgeResponse | null>(null);

  private bridgeHistorySubject = new BehaviorSubject<BridgeHistory[]>([]);
  bridgeHistory$ = this.bridgeHistorySubject.asObservable();

  constructor(
    private http: HttpClient,
    private supabaseService: SupabaseService,
    private web3Service: Web3WalletService
  ) {
    this.logConfiguration();
  }

  private logConfiguration(): void {
    console.log('TokenBridgeService initialized', {
      backendUrl: this.backendUrl,
      bridgeUrl: this.bridgeUrl,
      bridgeStatusUrl: this.bridgeStatusUrl,
      bridgeHistoryUrl: this.bridgeHistoryUrl
    });
  }

  /**
   * Get available balance to bridge from Supabase
   * This is the M-Pesa purchased tokens that haven't been bridged yet
   */
  async getAvailableSupabaseBalance(farmiqId: string): Promise<number> {
    try {
      const response = await this.http
        .get<{ available_balance: number }>(
          `${this.backendUrl}v1/bridge/available/${farmiqId}`
        )
        .pipe(timeout(10000))
        .toPromise();

      return response?.available_balance || 0;
    } catch (error) {
      console.error('Error fetching available balance:', error);
      return 0;
    }
  }

  /**
   * Bridge tokens from Supabase to Hedera
   * 
   * Backend will:
   * 1. Verify user has sufficient balance in Supabase
   * 2. Create Hedera transaction to mint tokens to user's wallet
   * 3. Upon success, deduct from Supabase (atomically)
   * 4. Return transaction hash
   */
  bridgeTokensToHedera(request: BridgeRequest): Observable<BridgeResponse> {
    this.isBridging.set(true);
    this.bridgeError.set(null);
    this.bridgeSuccess.set(false);

    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    const payload = {
      farmiq_id: request.farmiqId,
      hedera_account_id: request.hederaAccountId,
      amount: request.amount,
      provider: request.provider
    };

    console.log('Initiating token bridge with payload:', payload);

    return this.http
      .post<BridgeResponse>(this.bridgeUrl, payload, { headers })
      .pipe(
        timeout(60000), // 60 second timeout for Hedera transaction
        tap((response) => {
          this.isBridging.set(false);
          this.bridgeSuccess.set(response.success);
          this.lastBridgeTransaction.set(response);

          if (response.success) {
            console.log('Bridge successful:', response);
          } else {
            this.bridgeError.set(response.message || 'Bridge failed');
          }
        }),
        catchError((error) => {
          this.isBridging.set(false);
          const errorMessage =
            error?.error?.detail ||
            error?.error?.message ||
            'Failed to bridge tokens to Hedera. Please try again.';

          this.bridgeError.set(errorMessage);
          console.error('Bridge error:', error);
          return throwError(() => new Error(errorMessage));
        })
      );
  }

  /**
   * Check bridge transaction status
   */
  checkBridgeStatus(transactionHash: string): Observable<any> {
    return this.http
      .get<any>(`${this.bridgeStatusUrl}/${transactionHash}`)
      .pipe(
        timeout(30000),
        catchError((error) => {
          console.error('Error checking bridge status:', error);
          return throwError(() => error);
        })
      );
  }

  /**
   * Get user's bridge history
   */
  getBridgeHistory(farmiqId: string): Observable<BridgeHistory[]> {
    return this.http
      .get<BridgeHistory[]>(`${this.bridgeHistoryUrl}/${farmiqId}`)
      .pipe(
        timeout(30000),
        tap((history) => {
          this.bridgeHistorySubject.next(history);
        }),
        catchError((error) => {
          console.error('Error fetching bridge history:', error);
          return throwError(() => error);
        })
      );
  }

  /**
   * Verify bridge transaction on both chains
   * Ensures tokens were successfully transferred on both Supabase and Hedera
   */
  async verifyBridgeTransaction(
    supabaseTxId: string,
    hederaTxHash: string
  ): Promise<{ supabaseVerified: boolean; hederaVerified: boolean }> {
    try {
      const response = await this.http
        .post<{
          supabase_verified: boolean;
          hedera_verified: boolean;
          message: string;
        }>(
          `${this.backendUrl}v1/bridge/verify`,
          { supabase_tx_id: supabaseTxId, hedera_tx_hash: hederaTxHash }
        )
        .pipe(timeout(30000))
        .toPromise();

      return {
        supabaseVerified: response?.supabase_verified || false,
        hederaVerified: response?.hedera_verified || false
      };
    } catch (error) {
      console.error('Error verifying bridge transaction:', error);
      return { supabaseVerified: false, hederaVerified: false };
    }
  }

  /**
   * Get bridge fee (percentage of bridged amount)
   * Backend determines fee based on network conditions
   */
  async getBridgeFee(amount: number): Promise<number> {
    try {
      const response = await this.http
        .get<{ fee: number; fee_percentage: number }>(
          `${this.backendUrl}v1/bridge/fee?amount=${amount}`
        )
        .pipe(timeout(10000))
        .toPromise();

      return response?.fee || 0;
    } catch (error) {
      console.error('Error fetching bridge fee:', error);
      return 0;
    }
  }

  /**
   * Clear bridge state (after successful bridge or user dismissal)
   */
  clearBridgeState(): void {
    this.isBridging.set(false);
    this.bridgeError.set(null);
    this.bridgeSuccess.set(false);
  }
}
