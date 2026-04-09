import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';

export interface UserAccount {
  id: string;
  name: string;
  email: string;
  role: 'farmer' | 'cooperative' | 'lender' | 'agent' | 'admin';
  status: 'active' | 'suspended' | 'banned';
  joinDate: Date;
  lastLogin?: Date;
  kycStatus: 'pending' | 'verified' | 'rejected';
}

export interface RoleAssignment {
  userId: string;
  userName: string;
  previousRole: string;
  newRole: string;
  assignedDate: Date;
  assignedBy: string;
}

export interface SystemMetrics {
  totalUsers: number;
  activeUsers: number;
  totalFarms: number;
  totalCooperatives: number;
  totalLenders: number;
  totalAgents: number;
  systemHealth: 'optimal' | 'good' | 'fair' | 'poor';
  uptime: number;
}

export interface DataGovernance {
  dataQuality: number;
  complianceStatus: string;
  lastAudit: Date;
  pendingIssues: number;
}

export interface ModelMetrics {
  modelVersion: string;
  accuracy: number;
  precision: number;
  recall: number;
  lastTrained: Date;
  performanceStatus: 'excellent' | 'good' | 'fair' | 'poor';
}

@Injectable({
  providedIn: 'root',
})
export class AdminService {
  private apiUrl = '/api/admin';

  // Signals for reactive state
  systemMetricsSignal = signal<SystemMetrics | null>(null);
  usersSignal = signal<UserAccount[]>([]);
  dataGovernanceSignal = signal<DataGovernance | null>(null);
  modelMetricsSignal = signal<ModelMetrics | null>(null);

  // BehaviorSubjects for backward compatibility
  private systemMetricsSubject = new BehaviorSubject<SystemMetrics | null>(null);
  private usersSubject = new BehaviorSubject<UserAccount[]>([]);

  systemMetrics$ = this.systemMetricsSubject.asObservable();
  users$ = this.usersSubject.asObservable();

  constructor(private http: HttpClient) {
    this.initializeData();
  }

  private initializeData(): void {
    this.getSystemMetrics().subscribe();
    this.getAllUsers().subscribe();
  }

  /**
   * Get system dashboard metrics
   */
  getSystemMetrics(): Observable<SystemMetrics> {
    return this.http.get<SystemMetrics>(`${this.apiUrl}/dashboard/metrics`).pipe(
      tap(metrics => {
        this.systemMetricsSignal.set(metrics);
        this.systemMetricsSubject.next(metrics);
      })
    );
  }

  /**
   * Get all users
   */
  getAllUsers(): Observable<UserAccount[]> {
    return this.http.get<UserAccount[]>(`${this.apiUrl}/users`).pipe(
      tap(users => {
        this.usersSignal.set(users);
        this.usersSubject.next(users);
      })
    );
  }

  /**
   * Get users by role
   */
  getUsersByRole(role: string): Observable<UserAccount[]> {
    return this.http.get<UserAccount[]>(`${this.apiUrl}/users/role/${role}`);
  }

  /**
   * Get user details
   */
  getUserDetails(userId: string): Observable<UserAccount> {
    return this.http.get<UserAccount>(`${this.apiUrl}/users/${userId}`);
  }

  /**
   * Assign role to user
   */
  assignRole(userId: string, role: string): Observable<RoleAssignment> {
    return this.http.post<RoleAssignment>(`${this.apiUrl}/users/${userId}/assign-role`, { role });
  }

  /**
   * Suspend user account
   */
  suspendUser(userId: string, reason: string): Observable<{ status: string; message: string }> {
    return this.http.post<{ status: string; message: string }>(`${this.apiUrl}/users/${userId}/suspend`, { reason });
  }

  /**
   * Reactivate user account
   */
  reactivateUser(userId: string): Observable<{ status: string; message: string }> {
    return this.http.post<{ status: string; message: string }>(`${this.apiUrl}/users/${userId}/reactivate`, {});
  }

  /**
   * Ban user account
   */
  banUser(userId: string, reason: string): Observable<{ status: string; message: string }> {
    return this.http.post<{ status: string; message: string }>(`${this.apiUrl}/users/${userId}/ban`, { reason });
  }

  /**
   * Get data governance status
   */
  getDataGovernance(): Observable<DataGovernance> {
    return this.http.get<DataGovernance>(`${this.apiUrl}/governance/status`).pipe(
      tap(governance => {
        this.dataGovernanceSignal.set(governance);
      })
    );
  }

  /**
   * Run compliance audit
   */
  runComplianceAudit(): Observable<{ auditId: string; status: string; issues: string[] }> {
    return this.http.post<{ auditId: string; status: string; issues: string[] }>(`${this.apiUrl}/governance/audit`, {});
  }

  /**
   * Get audit history
   */
  getAuditHistory(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/governance/audit-history`);
  }

  /**
   * Get AI model metrics
   */
  getModelMetrics(): Observable<ModelMetrics> {
    return this.http.get<ModelMetrics>(`${this.apiUrl}/models/metrics`).pipe(
      tap(metrics => {
        this.modelMetricsSignal.set(metrics);
      })
    );
  }

  /**
   * Retrain model
   */
  retrainModel(): Observable<{ trainingId: string; status: string; estimatedTime: string }> {
    return this.http.post<{ trainingId: string; status: string; estimatedTime: string }>(`${this.apiUrl}/models/retrain`, {});
  }

  /**
   * Get model training history
   */
  getTrainingHistory(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/models/training-history`);
  }

  /**
   * Get Hedera blockchain integration status
   */
  getHCSIntegration(): Observable<Record<string, any>> {
    return this.http.get<Record<string, any>>(`${this.apiUrl}/hcs/status`);
  }

  /**
   * Verify blockchain transactions
   */
  verifyBlockchainTransaction(transactionId: string): Observable<{ verified: boolean; details: Record<string, any> }> {
    return this.http.get<{ verified: boolean; details: Record<string, any> }>(`${this.apiUrl}/hcs/verify/${transactionId}`);
  }

  /**
   * Get tokenomics overview
   */
  getTokenomics(): Observable<Record<string, any>> {
    return this.http.get<Record<string, any>>(`${this.apiUrl}/tokenomics/overview`);
  }

  /**
   * Get token distribution
   */
  getTokenDistribution(): Observable<Record<string, number>> {
    return this.http.get<Record<string, number>>(`${this.apiUrl}/tokenomics/distribution`);
  }

  /**
   * Get payment processing status
   */
  getPaymentStatus(): Observable<Record<string, any>> {
    return this.http.get<Record<string, any>>(`${this.apiUrl}/payments/status`);
  }

  /**
   * Process payment
   */
  processPayment(paymentData: Record<string, any>): Observable<{ transactionId: string; status: string }> {
    return this.http.post<{ transactionId: string; status: string }>(`${this.apiUrl}/payments/process`, paymentData);
  }

  /**
   * Get payment transactions
   */
  getPaymentTransactions(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/payments/transactions`);
  }

  /**
   * Get reconciliation report
   */
  getReconciliationReport(): Observable<Record<string, any>> {
    return this.http.get<Record<string, any>>(`${this.apiUrl}/reconciliation/report`);
  }

  /**
   * Run reconciliation process
   */
  runReconciliation(): Observable<{ reconciliationId: string; status: string; discrepancies: number }> {
    return this.http.post<{ reconciliationId: string; status: string; discrepancies: number }>(`${this.apiUrl}/reconciliation/run`, {});
  }

  /**
   * Get reconciliation history
   */
  getReconciliationHistory(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/reconciliation/history`);
  }

  /**
   * Get user profile
   */
  getUserProfile(): Observable<any> {
    return this.http.get(`${this.apiUrl}/profile`);
  }

  /**
   * Get notifications
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
   * Mark specific notification as read
   */
  markNotificationAsRead(notifId: string): Observable<{ status: string }> {
    return this.http.post<{ status: string }>(`${this.apiUrl}/notifications/${notifId}/read`, {});
  }

  /**
   * Delete notification
   */
  deleteNotification(notifId: string): Observable<{ status: string }> {
    return this.http.delete<{ status: string }>(`${this.apiUrl}/notifications/${notifId}`);
  }

  /**
   * Logout admin
   */
  logout(): Observable<{ status: string }> {
    return this.http.post<{ status: string }>(`${this.apiUrl}/logout`, {});
  }
}
