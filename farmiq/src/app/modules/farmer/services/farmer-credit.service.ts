/**
 * Farmer Credit Service
 * Handles credit scoring, eligibility assessment, and loan applications
 */

import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';

export interface CreditScore {
  farmiquId: string;
  score: number; // 300-850
  riskLevel: 'very_low' | 'low' | 'medium' | 'high' | 'very_high';
  factors: CreditFactor[];
  lastUpdated: string;
  nextReviewDate: string;
}

export interface CreditFactor {
  name: string;
  weight: number; // 0-100 (percentage impact)
  currentValue: number;
  optimalValue: number;
  status: 'good' | 'fair' | 'needs_improvement';
  improvement?: string;
}

export interface LoanEligibility {
  isEligible: boolean;
  maxLoanAmount: number;
  interestRate: number;
  tenure: number; // months
  monthlyPayment: number;
  requiredDocuments: string[];
  reasons?: string[];
}

export interface LoanApplication {
  id: string;
  farmiquId: string;
  amount: number;
  tenure: number;
  purpose: string;
  status: 'draft' | 'submitted' | 'approved' | 'rejected' | 'active' | 'completed' | 'defaulted';
  appliedDate: string;
  approvalDate?: string;
  disbursementDate?: string;
  disbursedAmount?: number;
}

export interface PaymentSchedule {
  loanId: string;
  dueDate: string;
  amount: number;
  principal: number;
  interest: number;
  status: 'pending' | 'paid' | 'overdue' | 'defaulted';
  paidDate?: string;
  paidAmount?: number;
}

@Injectable({ providedIn: 'root' })
export class FarmerCreditService {
  private apiUrl = environment.apiUrl;
  private supabaseUrl = `${environment.supabase.url}/rest/v1`;

  // ========== STATE ==========
  creditScore = signal<CreditScore | null>(null);
  loanEligibility = signal<LoanEligibility | null>(null);
  loanHistory = signal<LoanApplication[]>([]);
  activeLoans = signal<LoanApplication[]>([]);
  paymentSchedule = signal<PaymentSchedule[]>([]);
  loading = signal<boolean>(false);
  error = signal<string | null>(null);

  // ========== COMPUTED VALUES ==========
  creditRating = computed(() => {
    const score = this.creditScore()?.score || 0;
    if (score >= 750) return 'Excellent';
    if (score >= 700) return 'Very Good';
    if (score >= 650) return 'Good';
    if (score >= 600) return 'Fair';
    return 'Poor';
  });

  totalLoanDebt = computed(() => {
    return this.activeLoans().reduce((sum, loan) => sum + loan.amount, 0);
  });

  nextPaymentDue = computed(() => {
    const schedule = this.paymentSchedule();
    return schedule.find(p => p.status === 'pending')?.dueDate || null;
  });

  overduePayments = computed(() => {
    return this.paymentSchedule().filter(p => p.status === 'overdue').length;
  });

  constructor(private http: HttpClient) {}

  /**
   * Get credit score for farmer
   */
  getCreditScore(farmiquId: string): Observable<CreditScore> {
    this.loading.set(true);
    return this.http.get<CreditScore>(
      `${this.apiUrl}/credit/score/${farmiquId}`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((score: CreditScore) => {
        this.creditScore.set(score);
        this.loading.set(false);
        this.error.set(null);
      }),
      catchError((err) => this.handleError('Failed to fetch credit score', err))
    );
  }

  /**
   * LOGIC: Calculate loan eligibility based on credit score and factors
   */
  calculateEligibility(farmiquId: string): Observable<LoanEligibility> {
    return this.http.get<LoanEligibility>(
      `${this.apiUrl}/credit/eligibility/${farmiquId}`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((eligibility: LoanEligibility) => {
        this.loanEligibility.set(eligibility);
      }),
      catchError((err) => this.handleError('Failed to calculate eligibility', err))
    );
  }

  /**
   * Get loan history (all loans)
   */
  getLoanHistory(farmiquId: string): Observable<LoanApplication[]> {
    return this.http.get<LoanApplication[]>(
      `${this.supabaseUrl}/loan_applications?farmiq_id=eq.${farmiquId}&order=applied_date.desc`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((loans: LoanApplication[]) => {
        this.loanHistory.set(loans);
        // Filter active loans
        const active = loans.filter(l => l.status === 'active');
        this.activeLoans.set(active);
      }),
      catchError((err) => this.handleError('Failed to fetch loan history', err))
    );
  }

  /**
   * Get payment schedule for active loans
   */
  getPaymentSchedule(loanId: string): Observable<PaymentSchedule[]> {
    return this.http.get<PaymentSchedule[]>(
      `${this.supabaseUrl}/repayment_schedules?loan_id=eq.${loanId}&order=due_date.asc`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((schedule: PaymentSchedule[]) => {
        this.paymentSchedule.set(schedule);
      }),
      catchError((err) => this.handleError('Failed to fetch payment schedule', err))
    );
  }

  /**
   * Apply for a loan
   */
  applyForLoan(farmiquId: string, application: Partial<LoanApplication>): Observable<LoanApplication> {
    const payload = {
      farmiq_id: farmiquId,
      amount: application.amount,
      tenure: application.tenure,
      purpose: application.purpose,
      status: 'draft',
      applied_date: new Date().toISOString()
    };

    return this.http.post<LoanApplication>(
      `${this.supabaseUrl}/loan_applications`,
      payload,
      { headers: this.getHeaders() }
    ).pipe(
      tap((loan: LoanApplication) => {
        // Add to history
        const updated = [...this.loanHistory(), loan];
        this.loanHistory.set(updated);
      }),
      catchError((err) => this.handleError('Failed to apply for loan', err))
    );
  }

  /**
   * Submit loan application for review
   */
  submitLoanApplication(loanId: string): Observable<LoanApplication> {
    return this.http.patch<LoanApplication>(
      `${this.supabaseUrl}/loan_applications?id=eq.${loanId}`,
      { status: 'submitted' },
      { headers: this.getHeaders() }
    ).pipe(
      catchError((err) => this.handleError('Failed to submit loan', err))
    );
  }

  /**
   * Record a loan payment
   */
  recordPayment(scheduleId: string, amount: number, paymentDate: string): Observable<PaymentSchedule> {
    const payload = {
      status: 'paid',
      paid_date: paymentDate,
      paid_amount: amount
    };

    return this.http.patch<PaymentSchedule>(
      `${this.supabaseUrl}/repayment_schedules?id=eq.${scheduleId}`,
      payload,
      { headers: this.getHeaders() }
    ).pipe(
      catchError((err) => this.handleError('Failed to record payment', err))
    );
  }

  /**
   * LOGIC: Calculate monthly payment
   * Using: P = L[c(1 + c)^n]/[(1 + c)^n - 1]
   * where: L = loan amount, c = monthly interest rate, n = number of months
   */
  calculateMonthlyPayment(loanAmount: number, annualRate: number, months: number): number {
    const monthlyRate = annualRate / 100 / 12;
    
    if (monthlyRate === 0) {
      return loanAmount / months;
    }

    const numerator = loanAmount * monthlyRate * Math.pow(1 + monthlyRate, months);
    const denominator = Math.pow(1 + monthlyRate, months) - 1;
    
    return Math.round((numerator / denominator) * 100) / 100;
  }

  /**
   * LOGIC: Determine loan eligibility based on credit score
   * Credit scoring model:
   * - Payment history: 35%
   * - Credit utilization: 30%
   * - Credit history length: 15%
   * - Credit mix: 10%
   * - New inquiries: 10%
   */
  private calculateCreditEligibility(score: CreditScore): boolean {
    const creditScore = score.score;
    
    // Minimum credit score for eligibility
    if (creditScore < 500) return false;

    // Must have at least 2 good factors
    const goodFactors = score.factors.filter(f => f.status === 'good').length;
    if (goodFactors < 2) return false;

    // No critical failures allowed
    const failures = score.factors.filter(f => f.status === 'needs_improvement' && f.weight > 20);
    if (failures.length > 1) return false;

    return true;
  }

  /**
   * LOGIC: Calculate max loan amount based on credit score and farm size
   */
  private calculateMaxLoanAmount(creditScore: number, farmSizeAcres: number): number {
    // Base: 50,000 per acre of farmland
    const farmBase = farmSizeAcres * 50000;

    // Credit score multiplier (300-850 scale)
    const scoreMultiplier = Math.max(0.3, (creditScore - 300) / 550);

    // Risk adjustment: higher score = higher amounts
    const riskAdjustment = creditScore >= 750 ? 1.5 : 
                          creditScore >= 700 ? 1.3 : 
                          creditScore >= 650 ? 1.0 : 0.7;

    return Math.round(farmBase * scoreMultiplier * riskAdjustment);
  }

  /**
   * Get HTTP headers
   */
  private getHeaders() {
    const token = sessionStorage.getItem('auth_token');
    return {
      'Authorization': `Bearer ${token || ''}`,
      'apikey': environment.supabase.anonKey,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Handle errors
   */
  private handleError(message: string, error: any) {
    console.error(message, error);
    this.error.set(message);
    this.loading.set(false);
    return throwError(() => error);
  }
}
