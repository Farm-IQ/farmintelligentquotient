import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';

export interface LoanApplication {
  id: string;
  farmerId: string;
  farmerName: string;
  amount: number;
  duration: number;
  interestRate: number;
  purpose: string;
  status: 'pending' | 'approved' | 'rejected' | 'active' | 'closed';
  riskScore: number;
  submissionDate: Date;
  decisionDate?: Date;
}

export interface RiskProfile {
  farmerId: string;
  farmerName: string;
  fiqScore: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  defaultRisk: number;
  collateralValue: number;
  recommendedLoanAmount: number;
}

export interface PortfolioMetrics {
  totalActiveLoans: number;
  totalLoanValue: number;
  defaultRate: number;
  averageInterestRate: number;
  portfolioHealth: 'excellent' | 'good' | 'fair' | 'poor';
}

export interface LoanDecision {
  loanId: string;
  decision: 'approve' | 'reject' | 'defer';
  reason: string;
  approvedAmount?: number;
  approvedInterestRate?: number;
  conditions?: string[];
}

@Injectable({
  providedIn: 'root',
})
export class LenderService {
  private apiUrl = '/api/lenders';

  // Signals for reactive state
  portfolioMetricsSignal = signal<PortfolioMetrics | null>(null);
  loanApplicationsSignal = signal<LoanApplication[]>([]);
  riskProfilesSignal = signal<RiskProfile[]>([]);

  // BehaviorSubjects for backward compatibility
  private portfolioMetricsSubject = new BehaviorSubject<PortfolioMetrics | null>(null);
  private loanApplicationsSubject = new BehaviorSubject<LoanApplication[]>([]);

  portfolioMetrics$ = this.portfolioMetricsSubject.asObservable();
  loanApplications$ = this.loanApplicationsSubject.asObservable();

  constructor(private http: HttpClient) {
    this.initializeData();
  }

  private initializeData(): void {
    this.getPortfolioMetrics().subscribe();
    this.getPendingApplications().subscribe();
  }

  /**
   * Get risk dashboard data for a farmer
   */
  getRiskProfile(farmerId: string): Observable<RiskProfile> {
    return this.http.get<RiskProfile>(`${this.apiUrl}/risk/${farmerId}`);
  }

  /**
   * Get all risk profiles in portfolio
   */
  getRiskProfiles(): Observable<RiskProfile[]> {
    return this.http.get<RiskProfile[]>(`${this.apiUrl}/risk/profiles`).pipe(
      tap(profiles => {
        this.riskProfilesSignal.set(profiles);
      })
    );
  }

  /**
   * Get pending loan applications
   */
  getPendingApplications(): Observable<LoanApplication[]> {
    return this.http.get<LoanApplication[]>(`${this.apiUrl}/loans/pending`).pipe(
      tap(applications => {
        this.loanApplicationsSignal.set(applications);
        this.loanApplicationsSubject.next(applications);
      })
    );
  }

  /**
   * Get all loan applications
   */
  getAllApplications(): Observable<LoanApplication[]> {
    return this.http.get<LoanApplication[]>(`${this.apiUrl}/loans/all`).pipe(
      tap(applications => {
        this.loanApplicationsSignal.set(applications);
        this.loanApplicationsSubject.next(applications);
      })
    );
  }

  /**
   * Get detailed loan application
   */
  getLoanApplication(loanId: string): Observable<LoanApplication> {
    return this.http.get<LoanApplication>(`${this.apiUrl}/loans/${loanId}`);
  }

  /**
   * Make loan decision (approve/reject)
   */
  makeLoanDecision(decision: LoanDecision): Observable<{ status: string; message: string }> {
    return this.http.post<{ status: string; message: string }>(`${this.apiUrl}/loans/decision`, decision);
  }

  /**
   * Get market insights
   */
  getMarketInsights(): Observable<Record<string, any>> {
    return this.http.get<Record<string, any>>(`${this.apiUrl}/insights/market`);
  }

  /**
   * Get portfolio performance metrics
   */
  getPortfolioMetrics(): Observable<PortfolioMetrics> {
    return this.http.get<PortfolioMetrics>(`${this.apiUrl}/portfolio/metrics`).pipe(
      tap(metrics => {
        this.portfolioMetricsSignal.set(metrics);
        this.portfolioMetricsSubject.next(metrics);
      })
    );
  }

  /**
   * Monitor active loan
   */
  monitorLoan(loanId: string): Observable<LoanApplication & { paymentStatus: Record<string, any> }> {
    return this.http.get<LoanApplication & { paymentStatus: Record<string, any> }>(`${this.apiUrl}/portfolio/loan/${loanId}`);
  }

  /**
   * Get payment schedule for loan
   */
  getPaymentSchedule(loanId: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/portfolio/loan/${loanId}/schedule`);
  }

  /**
   * Get lender wallet balance
   */
  getWalletBalance(): Observable<{ balance: number; currency: string }> {
    return this.http.get<{ balance: number; currency: string }>(`${this.apiUrl}/wallet/balance`);
  }

  /**
   * Transfer loan proceeds
   */
  transferLoanProceeds(loanId: string, amount: number, recipient: string): Observable<{ transactionId: string; status: string }> {
    return this.http.post<{ transactionId: string; status: string }>(`${this.apiUrl}/wallet/transfer`, { loanId, amount, recipient });
  }

  /**
   * Get wallet transactions
   */
  getWalletTransactions(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/wallet/transactions`);
  }

  /**
   * Get user profile for navbar
   */
  getUserProfile(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/profile`);
  }

  /**
   * Get notifications for navbar
   */
  getNotifications(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/notifications`);
  }

  /**
   * Mark all notifications as read
   */
  markNotificationsAsRead(): Observable<{ status: string }> {
    return this.http.post<{ status: string }>(`${this.apiUrl}/notifications/mark-all-read`, {});
  }

  /**
   * Mark single notification as read
   */
  markNotificationAsRead(notificationId: string): Observable<{ status: string }> {
    return this.http.post<{ status: string }>(`${this.apiUrl}/notifications/${notificationId}/read`, {});
  }

  /**
   * Delete a notification
   */
  deleteNotification(notificationId: string): Observable<{ status: string }> {
    return this.http.delete<{ status: string }>(`${this.apiUrl}/notifications/${notificationId}`);
  }

  /**
   * Logout
   */
  logout(): Observable<{ status: string }> {
    return this.http.post<{ status: string }>(`${this.apiUrl}/logout`, {});
  }
}
