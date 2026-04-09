import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { AgentWallet, AgentWithdrawalRequest } from '../models/agent.model';

@Injectable({
  providedIn: 'root',
})
export class AgentWalletService {
  private apiUrl = '/api/agents';

  // Signals for wallet state
  walletDataSignal = signal<AgentWallet | null>(null);
  isLoadingSignal = signal<boolean>(false);
  withdrawalHistorySignal = signal<AgentWithdrawalRequest[]>([]);

  // BehaviorSubjects for backward compatibility
  private walletDataSubject = new BehaviorSubject<AgentWallet | null>(null);
  private withdrawalHistorySubject = new BehaviorSubject<AgentWithdrawalRequest[]>([]);

  public walletData$ = this.walletDataSubject.asObservable();
  public withdrawalHistory$ = this.withdrawalHistorySubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Get agent wallet data
   * FIXED: Returns Observable<AgentWallet> not array
   */
  getWallet(agentId: string): Observable<AgentWallet> {
    this.isLoadingSignal.set(true);

    return this.http
      .get<AgentWallet>(`${this.apiUrl}/${agentId}/wallet`)
      .pipe(
        tap((wallet) => {
          this.walletDataSignal.set(wallet);
          this.walletDataSubject.next(wallet);
          this.isLoadingSignal.set(false);
        }),
        catchError((error) => {
          this.isLoadingSignal.set(false);
          console.error('Error fetching wallet:', error);
          throw error;
        })
      );
  }

  /**
   * Get wallet balance
   */
  getBalance(agentId: string): Observable<number> {
    return this.http.get<number>(`${this.apiUrl}/${agentId}/wallet/balance`);
  }

  /**
   * Get available balance (balance - locked)
   */
  getAvailableBalance(agentId: string): Observable<number> {
    return this.http.get<number>(
      `${this.apiUrl}/${agentId}/wallet/available-balance`
    );
  }

  /**
   * Request withdrawal
   */
  requestWithdrawal(
    agentId: string,
    request: {
      amount: number;
      bankAccount: string;
      notes?: string;
    }
  ): Observable<AgentWithdrawalRequest> {
    return this.http
      .post<AgentWithdrawalRequest>(
        `${this.apiUrl}/${agentId}/wallet/withdraw`,
        request
      )
      .pipe(
        tap((result) => {
          this.getWithdrawalHistory(agentId).subscribe();
        })
      );
  }

  /**
   * Get withdrawal history
   */
  getWithdrawalHistory(agentId: string): Observable<AgentWithdrawalRequest[]> {
    return this.http
      .get<AgentWithdrawalRequest[]>(
        `${this.apiUrl}/${agentId}/wallet/withdrawals`
      )
      .pipe(
        tap((history) => {
          this.withdrawalHistorySignal.set(history);
          this.withdrawalHistorySubject.next(history);
        })
      );
  }

  /**
   * Get withdrawal request status
   */
  getWithdrawalStatus(
    agentId: string,
    withdrawalId: string
  ): Observable<AgentWithdrawalRequest> {
    return this.http.get<AgentWithdrawalRequest>(
      `${this.apiUrl}/${agentId}/wallet/withdrawals/${withdrawalId}`
    );
  }

  /**
   * Add funds to wallet (admin only)
   */
  addFunds(
    agentId: string,
    amount: number,
    reason: string
  ): Observable<AgentWallet> {
    return this.http
      .post<AgentWallet>(`${this.apiUrl}/${agentId}/wallet/add-funds`, {
        amount,
        reason,
      })
      .pipe(
        tap((wallet) => {
          this.walletDataSignal.set(wallet);
          this.walletDataSubject.next(wallet);
        })
      );
  }

  /**
   * Deduct funds from wallet (for loan repayment, etc.)
   */
  deductFunds(
    agentId: string,
    amount: number,
    reason: string
  ): Observable<AgentWallet> {
    return this.http
      .post<AgentWallet>(`${this.apiUrl}/${agentId}/wallet/deduct`, {
        amount,
        reason,
      })
      .pipe(
        tap((wallet) => {
          this.walletDataSignal.set(wallet);
          this.walletDataSubject.next(wallet);
        })
      );
  }

  /**
   * Lock funds (for pending transactions)
   */
  lockFunds(agentId: string, amount: number): Observable<AgentWallet> {
    return this.http
      .post<AgentWallet>(`${this.apiUrl}/${agentId}/wallet/lock`, { amount })
      .pipe(
        tap((wallet) => {
          this.walletDataSignal.set(wallet);
          this.walletDataSubject.next(wallet);
        })
      );
  }

  /**
   * Unlock funds
   */
  unlockFunds(agentId: string, amount: number): Observable<AgentWallet> {
    return this.http
      .post<AgentWallet>(`${this.apiUrl}/${agentId}/wallet/unlock`, { amount })
      .pipe(
        tap((wallet) => {
          this.walletDataSignal.set(wallet);
          this.walletDataSubject.next(wallet);
        })
      );
  }

  /**
   * Get wallet transactions
   */
  getTransactions(
    agentId: string,
    limit: number = 50
  ): Observable<
    Array<{
      id: string;
      type: string;
      amount: number;
      description: string;
      timestamp: Date;
      balanceAfter: number;
    }>
  > {
    return this.http.get<
      Array<{
        id: string;
        type: string;
        amount: number;
        description: string;
        timestamp: Date;
        balanceAfter: number;
      }>
    >(`${this.apiUrl}/${agentId}/wallet/transactions?limit=${limit}`);
  }

  /**
   * Get current wallet from signal
   */
  getCurrentWallet(): AgentWallet | null {
    return this.walletDataSignal();
  }

  /**
   * Check if loading
   */
  isLoading(): boolean {
    return this.isLoadingSignal();
  }
}
