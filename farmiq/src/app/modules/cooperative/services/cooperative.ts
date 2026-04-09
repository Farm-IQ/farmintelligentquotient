import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';

export interface CooperativeMember {
  id: string;
  name: string;
  email: string;
  joinDate: Date;
  status: 'active' | 'inactive' | 'suspended';
  farmSize: number;
  creditScore?: number;
}

export interface CooperativeData {
  id?: string;
  name: string;
  location: string;
  totalMembers: number;
  totalAcreage: number;
  registrationDate: Date;
}

export interface BulkScoringResult {
  membersScored: number;
  averageScore: number;
  highRiskMembers: number;
  timestamp: Date;
}

export interface CooperativeInsights {
  totalRevenue: number;
  memberRetention: number;
  averageCreditScore: number;
  topCommodities: string[];
  marketTrends: Record<string, number>;
}

@Injectable({
  providedIn: 'root',
})
export class CooperativeService {
  private apiUrl = '/api/cooperatives';

  // Signals for reactive state
  cooperativeDataSignal = signal<CooperativeData | null>(null);
  membersSignal = signal<CooperativeMember[]>([]);
  insightsSignal = signal<CooperativeInsights | null>(null);

  // BehaviorSubjects for backward compatibility
  private cooperativeDataSubject = new BehaviorSubject<CooperativeData | null>(null);
  private membersSubject = new BehaviorSubject<CooperativeMember[]>([]);

  cooperativeData$ = this.cooperativeDataSubject.asObservable();
  members$ = this.membersSubject.asObservable();

  constructor(private http: HttpClient) {
    this.initializeData();
  }

  private initializeData(): void {
    this.getCooperativeData().subscribe(data => {
      this.cooperativeDataSignal.set(data);
      this.cooperativeDataSubject.next(data);
    });
    this.getMembers().subscribe();
  }

  /**
   * Get cooperative data
   */
  getCooperativeData(): Observable<CooperativeData> {
    return this.http.get<CooperativeData>(`${this.apiUrl}/data`).pipe(
      tap(data => {
        this.cooperativeDataSignal.set(data);
        this.cooperativeDataSubject.next(data);
      })
    );
  }

  /**
   * Update cooperative data
   */
  updateCooperativeData(data: CooperativeData): Observable<CooperativeData> {
    return this.http.put<CooperativeData>(`${this.apiUrl}/data`, data).pipe(
      tap(updated => {
        this.cooperativeDataSignal.set(updated);
        this.cooperativeDataSubject.next(updated);
      })
    );
  }

  /**
   * Get all cooperative members
   */
  getMembers(): Observable<CooperativeMember[]> {
    return this.http.get<CooperativeMember[]>(`${this.apiUrl}/members`).pipe(
      tap(members => {
        this.membersSignal.set(members);
        this.membersSubject.next(members);
      })
    );
  }

  /**
   * Add member to cooperative
   */
  addMember(member: CooperativeMember): Observable<CooperativeMember> {
    return this.http.post<CooperativeMember>(`${this.apiUrl}/members`, member).pipe(
      tap(newMember => {
        const currentMembers = this.membersSignal();
        this.membersSignal.set([...currentMembers, newMember]);
        this.membersSubject.next([...currentMembers, newMember]);
      })
    );
  }

  /**
   * Remove member from cooperative
   */
  removeMember(memberId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/members/${memberId}`).pipe(
      tap(() => {
        const currentMembers = this.membersSignal().filter(m => m.id !== memberId);
        this.membersSignal.set(currentMembers);
        this.membersSubject.next(currentMembers);
      })
    );
  }

  /**
   * Update member status
   */
  updateMemberStatus(memberId: string, status: 'active' | 'inactive' | 'suspended'): Observable<CooperativeMember> {
    return this.http.patch<CooperativeMember>(`${this.apiUrl}/members/${memberId}`, { status });
  }

  /**
   * Run bulk FIQ credit scoring for all members
   */
  runBulkScoring(): Observable<BulkScoringResult> {
    return this.http.post<BulkScoringResult>(`${this.apiUrl}/scoring/bulk`, {});
  }

  /**
   * Get scoring history
   */
  getScoringHistory(): Observable<BulkScoringResult[]> {
    return this.http.get<BulkScoringResult[]>(`${this.apiUrl}/scoring/history`);
  }

  /**
   * Get cooperative insights
   */
  getInsights(): Observable<CooperativeInsights> {
    return this.http.get<CooperativeInsights>(`${this.apiUrl}/insights`).pipe(
      tap(insights => {
        this.insightsSignal.set(insights);
      })
    );
  }

  /**
   * Get cooperative financial overview
   */
  getFinancialOverview(): Observable<Record<string, any>> {
    return this.http.get<Record<string, any>>(`${this.apiUrl}/finance/overview`);
  }

  /**
   * Get group wallet balance
   */
  getGroupWalletBalance(): Observable<{ balance: number; currency: string }> {
    return this.http.get<{ balance: number; currency: string }>(`${this.apiUrl}/wallet/balance`);
  }

  /**
   * Distribute funds to members
   */
  distributeFunds(distribution: Record<string, number>): Observable<{ status: string; transactionId: string }> {
    return this.http.post<{ status: string; transactionId: string }>(`${this.apiUrl}/wallet/distribute`, { distribution });
  }

  /**
   * Get group transactions
   */
  getGroupTransactions(): Observable<any[]> {
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
