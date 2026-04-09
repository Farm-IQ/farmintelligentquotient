/**
 * Worker Payroll Service
 * Handles payroll calculations, salary processing, and payment tracking
 */

import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { tap, catchError, map } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';

export interface PayrollRecord {
  id: string;
  workerId: string;
  period: string; // YYYY-MM
  baseSalary: number;
  hoursWorked: number;
  overtimeHours: number;
  overtimePay: number;
  bonuses: number;
  deductions: PayrollDeduction[];
  totalDeductions: number;
  tax: number;
  netSalary: number;
  status: 'draft' | 'calculated' | 'processed' | 'paid';
  processedDate?: string;
  paymentDate?: string;
  paymentMethod?: 'bank_transfer' | 'mpesa' | 'cash' | 'cheque';
  reference?: string;
}

export interface PayrollDeduction {
  type: 'income_tax' | 'social_security' | 'health_insurance' | 'loan' | 'other';
  name: string;
  amount: number;
  percentage?: number; // if percentage-based
  notes?: string;
}

export interface PayrollSetting {
  workerId: string;
  hourlyRate?: number;
  overtimeMultiplier: number; // e.g., 1.5 for 150%
  taxBracket: 'low' | 'medium' | 'high';
  deductions: PayrollDeduction[];
  allowances?: Record<string, number>;
}

export interface PayrollReport {
  period: string;
  totalWorkers: number;
  totalBaseSalary: number;
  totalGross: number;
  totalDeductions: number;
  totalNetPayroll: number;
  totalTax: number;
  paidWorkers: number;
  pendingPayments: number;
}

@Injectable({ providedIn: 'root' })
export class WorkerPayrollService {
  private apiUrl = environment.apiUrl;
  private supabaseUrl = `${environment.supabase.url}/rest/v1`;

  // ========== STATE ==========
  payrollRecords = signal<PayrollRecord[]>([]);
  currentPayroll = signal<PayrollRecord | null>(null);
  payrollSettings = signal<PayrollSetting | null>(null);
  payrollReports = signal<PayrollReport[]>([]);
  loading = signal<boolean>(false);
  error = signal<string | null>(null);
  selectedPeriod = signal<string>('');

  // ========== COMPUTED ==========
  totalNetPayroll = computed(() => {
    return this.payrollRecords()
      .reduce((sum, record) => sum + record.netSalary, 0);
  });

  totalTaxDeduction = computed(() => {
    return this.payrollRecords()
      .reduce((sum, record) => sum + record.tax, 0);
  });

  averageNetSalary = computed(() => {
    const records = this.payrollRecords();
    if (records.length === 0) return 0;
    return this.totalNetPayroll() / records.length;
  });

  constructor(private http: HttpClient) {}

  /**
   * LOGIC: Calculate individual payroll
   * Formula: Gross = Base + Bonuses + OvertimePay - Deductions - Tax
   */
  calculatePayroll(
    baseSalary: number,
    hoursWorked: number,
    overtimeHours: number,
    bonuses: number = 0,
    deductions: PayrollDeduction[] = []
  ): Omit<PayrollRecord, 'id' | 'workerId' | 'period' | 'status' | 'processedDate' | 'paymentDate' | 'paymentMethod' | 'reference'> {
    
    // Constants for Kenya (can be parameterized)
    const STANDARD_HOURS = 160; // Monthly standard hours
    const HOURLY_RATE = 200; // KES per hour (example)
    const OVERTIME_RATE = HOURLY_RATE * 1.5; // 150% for overtime

    // Calculate components
    const overtimePay = overtimeHours > 0 
      ? Math.round(overtimeHours * OVERTIME_RATE * 100) / 100 
      : 0;

    const grossSalary = baseSalary + overtimePay + bonuses;

    // Calculate deductions
    const totalDeductions = deductions.reduce((sum, d) => sum + d.amount, 0);

    // LOGIC: Calculate income tax (progressive taxation)
    const tax = this.calculateIncomeTax(grossSalary);

    // Calculate net salary
    const netSalary = grossSalary - totalDeductions - tax;

    return {
      baseSalary,
      hoursWorked,
      overtimeHours,
      overtimePay: Math.round(overtimePay * 100) / 100,
      bonuses,
      deductions,
      totalDeductions,
      tax: Math.round(tax * 100) / 100,
      netSalary: Math.round(netSalary * 100) / 100
    };
  }

  /**
   * LOGIC: Calculate income tax using Kenya's progressive tax system (2024)
   * Brackets:
   * - 0 - 288,000: 10%
   * - 288,001 - 412,500: 15%
   * - 412,501 - 550,000: 20%
   * - 550,001+: 25%
   * Plus: Relief of 2,400 per month
   */
  private calculateIncomeTax(grossSalary: number): number {
    const TAX_RELIEF = 2400;
    let tax = 0;

    if (grossSalary <= 288000) {
      tax = (grossSalary * 0.10) - TAX_RELIEF;
    } else if (grossSalary <= 412500) {
      tax = (288000 * 0.10) + ((grossSalary - 288000) * 0.15) - TAX_RELIEF;
    } else if (grossSalary <= 550000) {
      tax = (288000 * 0.10) + 
            (124500 * 0.15) + 
            ((grossSalary - 412500) * 0.20) - TAX_RELIEF;
    } else {
      tax = (288000 * 0.10) + 
            (124500 * 0.15) + 
            (137500 * 0.20) + 
            ((grossSalary - 550000) * 0.25) - TAX_RELIEF;
    }

    return Math.max(0, tax); // Tax cannot be negative
  }

  /**
   * Get payroll for a specific period
   */
  getPayrollPeriod(period: string): Observable<PayrollRecord[]> {
    this.loading.set(true);
    return this.http.get<PayrollRecord[]>(
      `${this.supabaseUrl}/payroll?period=eq.${period}&order=worker_id.asc`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((records: PayrollRecord[]) => {
        this.payrollRecords.set(records);
        this.selectedPeriod.set(period);
        this.loading.set(false);
      }),
      catchError((err) => this.handleError('Failed to fetch payroll', err))
    );
  }

  /**
   * Get payroll for a specific worker
   */
  getWorkerPayroll(workerId: string, limit: number = 12): Observable<PayrollRecord[]> {
    return this.http.get<PayrollRecord[]>(
      `${this.supabaseUrl}/payroll?worker_id=eq.${workerId}&order=period.desc&limit=${limit}`,
      { headers: this.getHeaders() }
    ).pipe(
      catchError((err) => this.handleError('Failed to fetch worker payroll', err))
    );
  }

  /**
   * Save payroll record
   */
  savePayrollRecord(record: Partial<PayrollRecord>): Observable<PayrollRecord> {
    const payload = {
      worker_id: record.workerId,
      period: record.period,
      base_salary: record.baseSalary,
      hours_worked: record.hoursWorked,
      overtime_hours: record.overtimeHours,
      overtime_pay: record.overtimePay,
      bonuses: record.bonuses,
      deductions: record.deductions,
      total_deductions: record.totalDeductions,
      tax: record.tax,
      net_salary: record.netSalary,
      status: record.status || 'draft'
    };

    return this.http.post<PayrollRecord>(
      `${this.supabaseUrl}/payroll`,
      payload,
      { headers: this.getHeaders() }
    ).pipe(
      tap((savedRecord: PayrollRecord) => {
        const updated = [...this.payrollRecords(), savedRecord];
        this.payrollRecords.set(updated);
      }),
      catchError((err) => this.handleError('Failed to save payroll', err))
    );
  }

  /**
   * LOGIC: Process payroll for a period
   * Updates all draft records to calculated status
   * Prepares for payment processing
   */
  processPayroll(period: string, processedBy: string): Observable<PayrollReport> {
    return this.http.post<PayrollReport>(
      `${this.apiUrl}/payroll/process`,
      { period, processed_by: processedBy },
      { headers: this.getHeaders() }
    ).pipe(
      tap((report: PayrollReport) => {
        // Update all records status to 'processed'
        const updated = this.payrollRecords().map(r => ({
          ...r,
          status: 'processed' as const,
          processedDate: new Date().toISOString()
        }));
        this.payrollRecords.set(updated);
      }),
      catchError((err) => this.handleError('Failed to process payroll', err))
    );
  }

  /**
   * LOGIC: Process salary payment
   * Marks record as paid, records payment method and date
   */
  processSalaryPayment(
    recordId: string,
    paymentMethod: PayrollRecord['paymentMethod'],
    reference: string
  ): Observable<PayrollRecord> {
    const payload = {
      status: 'paid',
      payment_date: new Date().toISOString(),
      payment_method: paymentMethod,
      reference
    };

    return this.http.patch<PayrollRecord>(
      `${this.supabaseUrl}/payroll?id=eq.${recordId}`,
      payload,
      { headers: this.getHeaders() }
    ).pipe(
      tap((updated: PayrollRecord) => {
        const records = this.payrollRecords().map(r => r.id === recordId ? updated : r);
        this.payrollRecords.set(records);
      }),
      catchError((err) => this.handleError('Failed to process payment', err))
    );
  }

  /**
   * Get payroll report for a period
   */
  getPayrollReport(period: string): Observable<PayrollReport> {
    return this.http.get<PayrollReport>(
      `${this.apiUrl}/payroll/report?period=${period}`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((report: PayrollReport) => {
        const reports = this.payrollReports();
        this.payrollReports.set([...reports, report]);
      }),
      catchError((err) => this.handleError('Failed to fetch report', err))
    );
  }

  /**
   * Export payroll to CSV
   */
  exportPayrollCSV(period: string): Observable<Blob> {
    return this.http.get(
      `${this.apiUrl}/payroll/export?period=${period}&format=csv`,
      { responseType: 'blob', headers: this.getHeaders() }
    ).pipe(
      catchError((err) => this.handleError('Failed to export payroll', err))
    );
  }

  /**
   * Get payroll settings for a worker
   */
  getPayrollSettings(workerId: string): Observable<PayrollSetting> {
    return this.http.get<PayrollSetting[]>(
      `${this.supabaseUrl}/payroll_settings?worker_id=eq.${workerId}`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((settings: PayrollSetting[]) => {
        if (settings.length > 0) {
          this.payrollSettings.set(settings[0]);
        }
      }),
      map((settings: PayrollSetting[]) => settings[0] || {} as PayrollSetting),
      catchError((err) => this.handleError('Failed to fetch settings', err))
    );
  }

  /**
   * Get current month period string (YYYY-MM format)
   */
  getCurrentPeriod(): string {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    return `${year}-${month}`;
  }

  /**
   * Get previous month period
   */
  getPreviousPeriod(months: number = 1): string {
    const date = new Date();
    date.setMonth(date.getMonth() - months);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    return `${year}-${month}`;
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
