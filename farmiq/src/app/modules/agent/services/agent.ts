import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { signal } from '@angular/core';
import { tap } from 'rxjs/operators';

export interface FarmerOnboarding {
  id?: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  location: string;
  farmSize: number;
  cropType: string;
  bankAccount?: string;
  idNumber: string;
  status: 'pending' | 'verified' | 'rejected';
}

export interface KYCVerification {
  farmerId: string;
  farmerName: string;
  idVerified: boolean;
  addressVerified: boolean;
  phoneVerified: boolean;
  bankVerified: boolean;
  status: 'pending' | 'approved' | 'rejected';
  verificationDate?: Date;
  verificationNotes?: string;
}

export interface AgentPerformance {
  totalFarmersOnboarded: number;
  totalVerified: number;
  pendingVerification: number;
  verificationRate: number;
  commissionEarned: number;
  topPerformanceMonth: string;
}

export interface AgentCommission {
  month: string;
  totalOnboarded: number;
  totalVerified: number;
  baseCommission: number;
  bonusCommission: number;
  totalCommission: number;
  status: 'pending' | 'paid';
}

@Injectable({
  providedIn: 'root',
})
export class AgentService {
  private apiUrl = '/api/agents';

  // Signals for reactive state
  performanceSignal = signal<AgentPerformance | null>(null);
  onboardingListSignal = signal<FarmerOnboarding[]>([]);
  verificationsSignal = signal<KYCVerification[]>([]);

  // BehaviorSubjects for backward compatibility
  private performanceSubject = new BehaviorSubject<AgentPerformance | null>(null);
  private onboardingListSubject = new BehaviorSubject<FarmerOnboarding[]>([]);

  performance$ = this.performanceSubject.asObservable();
  onboardingList$ = this.onboardingListSubject.asObservable();

  constructor(private http: HttpClient) {
    this.initializeData();
  }

  private initializeData(): void {
    this.getPerformance().subscribe();
    this.getOnboardingList().subscribe();
  }

  /**
   * Register new farmer (onboarding)
   */
  onboardFarmer(farmerData: FarmerOnboarding): Observable<FarmerOnboarding> {
    return this.http.post<FarmerOnboarding>(`${this.apiUrl}/farmers/onboard`, farmerData).pipe(
      tap(farmer => {
        const currentList = this.onboardingListSignal();
        this.onboardingListSignal.set([...currentList, farmer]);
        this.onboardingListSubject.next([...currentList, farmer]);
      })
    );
  }

  /**
   * Get list of farmers onboarded by this agent
   */
  getOnboardingList(): Observable<FarmerOnboarding[]> {
    return this.http.get<FarmerOnboarding[]>(`${this.apiUrl}/farmers/onboarded`).pipe(
      tap(farmers => {
        this.onboardingListSignal.set(farmers);
        this.onboardingListSubject.next(farmers);
      })
    );
  }

  /**
   * Get pending farmer onboardings
   */
  getPendingOnboardings(): Observable<FarmerOnboarding[]> {
    return this.http.get<FarmerOnboarding[]>(`${this.apiUrl}/farmers/pending`);
  }

  /**
   * Update onboarding status
   */
  updateOnboardingStatus(farmerId: string, status: 'pending' | 'verified' | 'rejected'): Observable<FarmerOnboarding> {
    return this.http.patch<FarmerOnboarding>(`${this.apiUrl}/farmers/${farmerId}/status`, { status });
  }

  /**
   * Get KYC verification list
   */
  getVerifications(): Observable<KYCVerification[]> {
    return this.http.get<KYCVerification[]>(`${this.apiUrl}/verifications`).pipe(
      tap(verifications => {
        this.verificationsSignal.set(verifications);
      })
    );
  }

  /**
   * Get pending verifications
   */
  getPendingVerifications(): Observable<KYCVerification[]> {
    return this.http.get<KYCVerification[]>(`${this.apiUrl}/verifications/pending`);
  }

  /**
   * Submit KYC verification
   */
  submitVerification(verification: KYCVerification): Observable<KYCVerification> {
    return this.http.post<KYCVerification>(`${this.apiUrl}/verifications`, verification);
  }

  /**
   * Verify farmer identity
   */
  verifyFarmerIdentity(farmerId: string, verificationData: Record<string, any>): Observable<{ status: string; message: string }> {
    return this.http.post<{ status: string; message: string }>(`${this.apiUrl}/verify/identity/${farmerId}`, verificationData);
  }

  /**
   * Get agent performance report
   */
  getPerformance(): Observable<AgentPerformance> {
    return this.http.get<AgentPerformance>(`${this.apiUrl}/performance`).pipe(
      tap(performance => {
        this.performanceSignal.set(performance);
        this.performanceSubject.next(performance);
      })
    );
  }

  /**
   * Get detailed performance report
   */
  getDetailedReport(): Observable<Record<string, any>> {
    return this.http.get<Record<string, any>>(`${this.apiUrl}/reports/detailed`);
  }

  /**
   * Get monthly performance
   */
  getMonthlyPerformance(month: string): Observable<Record<string, any>> {
    return this.http.get<Record<string, any>>(`${this.apiUrl}/reports/monthly/${month}`);
  }

  /**
   * Get commission breakdown
   */
  getCommissionHistory(): Observable<AgentCommission[]> {
    return this.http.get<AgentCommission[]>(`${this.apiUrl}/commission/history`);
  }

  /**
   * Get wallet balance (commission wallet)
   */
  getWalletBalance(): Observable<{ balance: number; currency: string }> {
    return this.http.get<{ balance: number; currency: string }>(`${this.apiUrl}/wallet/balance`);
  }

  /**
   * Withdraw commission
   */
  withdrawCommission(amount: number, bankAccount: string): Observable<{ transactionId: string; status: string }> {
    return this.http.post<{ transactionId: string; status: string }>(`${this.apiUrl}/wallet/withdraw`, { amount, bankAccount });
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
   * Logout agent
   */
  logout(): Observable<{ status: string }> {
    return this.http.post<{ status: string }>(`${this.apiUrl}/logout`, {});
  }
}
