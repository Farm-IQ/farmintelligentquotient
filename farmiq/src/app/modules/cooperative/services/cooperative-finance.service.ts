import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import { CooperativeFinance } from '../models/cooperative.model';

@Injectable({
  providedIn: 'root',
})
export class CooperativeFinanceService {
  private apiUrl = '/api/cooperatives';

  // Signals for finance state
  financeDataSignal = signal<CooperativeFinance | null>(null);
  isLoadingSignal = signal<boolean>(false);

  // BehaviorSubjects for backward compatibility
  private financeDataSubject = new BehaviorSubject<CooperativeFinance | null>(null);
  private isLoadingSubject = new BehaviorSubject<boolean>(false);

  public financeData$ = this.financeDataSubject.asObservable();
  public isLoading$ = this.isLoadingSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Get cooperative finance data
   * FIXED: Returns Observable<CooperativeFinance> not array
   */
  getFinanceData(cooperativeId: string): Observable<CooperativeFinance> {
    this.isLoadingSignal.set(true);
    this.isLoadingSubject.next(true);

    return this.http
      .get<CooperativeFinance>(`${this.apiUrl}/${cooperativeId}/finance`)
      .pipe(
        tap((data) => {
          this.financeDataSignal.set(data);
          this.financeDataSubject.next(data);
          this.isLoadingSignal.set(false);
          this.isLoadingSubject.next(false);
        }),
        catchError((error) => {
          this.isLoadingSignal.set(false);
          this.isLoadingSubject.next(false);
          console.error('Error fetching finance data:', error);
          throw error;
        })
      );
  }

  /**
   * Update cooperative finance data
   */
  updateFinanceData(
    cooperativeId: string,
    data: Partial<CooperativeFinance>
  ): Observable<CooperativeFinance> {
    return this.http
      .put<CooperativeFinance>(
        `${this.apiUrl}/${cooperativeId}/finance`,
        data
      )
      .pipe(
        tap((updated) => {
          this.financeDataSignal.set(updated);
          this.financeDataSubject.next(updated);
        })
      );
  }

  /**
   * Get finance history for period
   */
  getFinanceHistory(
    cooperativeId: string,
    period: 'monthly' | 'quarterly' | 'annual',
    months: number = 12
  ): Observable<CooperativeFinance[]> {
    return this.http.get<CooperativeFinance[]>(
      `${this.apiUrl}/${cooperativeId}/finance/history?period=${period}&months=${months}`
    );
  }

  /**
   * Get financial summary
   */
  getFinancialSummary(cooperativeId: string): Observable<{
    totalRevenue: number;
    totalExpenses: number;
    netProfit: number;
    profitMargin: number;
    outstandingLoans: number;
  }> {
    return this.http.get<{
      totalRevenue: number;
      totalExpenses: number;
      netProfit: number;
      profitMargin: number;
      outstandingLoans: number;
    }>(`${this.apiUrl}/${cooperativeId}/finance/summary`);
  }

  /**
   * Record transaction
   */
  recordTransaction(
    cooperativeId: string,
    transaction: {
      type: 'debit' | 'credit';
      amount: number;
      description: string;
      category: string;
    }
  ): Observable<CooperativeFinance> {
    return this.http
      .post<CooperativeFinance>(
        `${this.apiUrl}/${cooperativeId}/finance/transaction`,
        transaction
      )
      .pipe(
        tap((updated) => {
          this.financeDataSignal.set(updated);
          this.financeDataSubject.next(updated);
        })
      );
  }

  /**
   * Get current finance data from signal
   */
  getCurrentFinanceData(): CooperativeFinance | null {
    return this.financeDataSignal();
  }

  /**
   * Check if loading
   */
  isLoading(): boolean {
    return this.isLoadingSignal();
  }
}
