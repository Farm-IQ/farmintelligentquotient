import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import { FarmCost, FarmRevenue, FarmFinancialSummary, FarmOperation } from '../models/livestock-operations.models';

/**
 * FarmFinancialService
 * Manages farm financial operations including costs, revenue, and profitability analysis
 */
@Injectable({
  providedIn: 'root'
})
export class FarmFinancialService {
  private apiUrl = '/api/farm-financial';
  private costsSubject = new BehaviorSubject<FarmCost[]>([]);
  public costs$ = this.costsSubject.asObservable();

  private revenueSubject = new BehaviorSubject<FarmRevenue[]>([]);
  public revenue$ = this.revenueSubject.asObservable();

  private summarySubject = new BehaviorSubject<FarmFinancialSummary | null>(null);
  public summary$ = this.summarySubject.asObservable();

  private operationsSubject = new BehaviorSubject<FarmOperation[]>([]);
  public operations$ = this.operationsSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Get all farm operations for a farm
   */
  getFarmOperations(farmId: string): Observable<FarmOperation[]> {
    return this.http.get<FarmOperation[]>(`${this.apiUrl}/farms/${farmId}/operations`).pipe(
      tap(operations => {
        this.operationsSubject.next(operations);
        console.log(`✅ Loaded ${operations.length} farm operations`);
      }),
      catchError(err => throwError(() => new Error(`Failed to load farm operations: ${err.message}`)))
    );
  }

  /**
   * Create a new farm operation (crop, dairy, beef, etc.)
   */
  createFarmOperation(farmId: string, operation: Partial<FarmOperation>): Observable<FarmOperation> {
    return this.http.post<FarmOperation>(`${this.apiUrl}/farms/${farmId}/operations`, operation).pipe(
      tap(created => {
        const current = this.operationsSubject.value;
        this.operationsSubject.next([...current, created]);
        console.log(`✅ Farm operation created: ${created.operationName}`);
      }),
      catchError(err => throwError(() => new Error(`Failed to create farm operation: ${err.message}`)))
    );
  }

  /**
   * Record farm cost (input expenses, labor, equipment, etc.)
   */
  recordCost(operationId: string, cost: Partial<FarmCost>): Observable<FarmCost> {
    return this.http.post<FarmCost>(`${this.apiUrl}/operations/${operationId}/costs`, cost).pipe(
      tap(created => {
        const current = this.costsSubject.value;
        this.costsSubject.next([...current, created]);
        console.log(`✅ Cost recorded: ${cost.description} - ${cost.amount}`);
      }),
      catchError(err => throwError(() => new Error(`Failed to record cost: ${err.message}`)))
    );
  }

  /**
   * Get costs for a specific operation or period
   */
  getOperationCosts(operationId: string, filters?: { startDate?: string; endDate?: string; costType?: string }): Observable<FarmCost[]> {
    let url = `${this.apiUrl}/operations/${operationId}/costs`;
    if (filters) {
      const params = new URLSearchParams();
      if (filters.startDate) params.append('startDate', filters.startDate);
      if (filters.endDate) params.append('endDate', filters.endDate);
      if (filters.costType) params.append('costType', filters.costType);
      if (params.toString()) url += `?${params.toString()}`;
    }
    return this.http.get<FarmCost[]>(url).pipe(
      tap(costs => this.costsSubject.next(costs)),
      catchError(err => throwError(() => new Error(`Failed to load operation costs: ${err.message}`)))
    );
  }

  /**
   * Record farm revenue (sales of produce, livestock products, etc.)
   */
  recordRevenue(operationId: string, revenue: Partial<FarmRevenue>): Observable<FarmRevenue> {
    return this.http.post<FarmRevenue>(`${this.apiUrl}/operations/${operationId}/revenue`, revenue).pipe(
      tap(created => {
        const current = this.revenueSubject.value;
        this.revenueSubject.next([...current, created]);
        console.log(`✅ Revenue recorded: ${revenue.buyerName} - ${revenue.totalRevenue}`);
      }),
      catchError(err => throwError(() => new Error(`Failed to record revenue: ${err.message}`)))
    );
  }

  /**
   * Get revenue for a specific operation or period
   */
  getOperationRevenue(operationId: string, filters?: { startDate?: string; endDate?: string; buyerType?: string }): Observable<FarmRevenue[]> {
    let url = `${this.apiUrl}/operations/${operationId}/revenue`;
    if (filters) {
      const params = new URLSearchParams();
      if (filters.startDate) params.append('startDate', filters.startDate);
      if (filters.endDate) params.append('endDate', filters.endDate);
      if (filters.buyerType) params.append('buyerType', filters.buyerType);
      if (params.toString()) url += `?${params.toString()}`;
    }
    return this.http.get<FarmRevenue[]>(url).pipe(
      tap(revenue => this.revenueSubject.next(revenue)),
      catchError(err => throwError(() => new Error(`Failed to load operation revenue: ${err.message}`)))
    );
  }

  /**
   * Get financial summary for a farm (profitability analysis)
   */
  getFarmFinancialSummary(farmId: string, filters?: { startDate?: string; endDate?: string }): Observable<FarmFinancialSummary> {
    let url = `${this.apiUrl}/farms/${farmId}/summary`;
    if (filters) {
      const params = new URLSearchParams();
      if (filters.startDate) params.append('startDate', filters.startDate);
      if (filters.endDate) params.append('endDate', filters.endDate);
      if (params.toString()) url += `?${params.toString()}`;
    }
    return this.http.get<FarmFinancialSummary>(url).pipe(
      tap(summary => {
        this.summarySubject.next(summary);
        console.log(`✅ Financial summary: Revenue=${summary.totalRevenue}, Costs=${summary.totalCosts}, ROI=${summary.roiPercentage}%`);
      }),
      catchError(err => throwError(() => new Error(`Failed to load financial summary: ${err.message}`)))
    );
  }

  /**
   * Get operation-specific financial summary
   */
  getOperationFinancialSummary(operationId: string, filters?: { startDate?: string; endDate?: string }): Observable<any> {
    let url = `${this.apiUrl}/operations/${operationId}/summary`;
    if (filters) {
      const params = new URLSearchParams();
      if (filters.startDate) params.append('startDate', filters.startDate);
      if (filters.endDate) params.append('endDate', filters.endDate);
      if (params.toString()) url += `?${params.toString()}`;
    }
    return this.http.get(url).pipe(
      catchError(err => throwError(() => new Error(`Failed to load operation financial summary: ${err.message}`)))
    );
  }

  /**
   * Calculate break-even analysis for an operation
   */
  calculateBreakEven(operationId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/operations/${operationId}/break-even`).pipe(
      tap(result => console.log(`✅ Break-even calculation completed for operation ${operationId}`)),
      catchError(err => throwError(() => new Error(`Failed to calculate break-even: ${err.message}`)))
    );
  }

  /**
   * Compare profitability between operations
   */
  compareOperationsProfitability(farmId: string, startDate?: string, endDate?: string): Observable<any> {
    let url = `${this.apiUrl}/farms/${farmId}/operations/compare-profitability`;
    if (startDate || endDate) {
      const params = new URLSearchParams();
      if (startDate) params.append('startDate', startDate);
      if (endDate) params.append('endDate', endDate);
      url += `?${params.toString()}`;
    }
    return this.http.get(url).pipe(
      catchError(err => throwError(() => new Error(`Failed to compare operations: ${err.message}`)))
    );
  }

  /**
   * Get financial trends (monthly/quarterly/yearly)
   */
  getFinancialTrends(farmId: string, period: 'monthly' | 'quarterly' | 'yearly', filters?: { startDate?: string; endDate?: string }): Observable<any[]> {
    let url = `${this.apiUrl}/farms/${farmId}/trends?period=${period}`;
    if (filters) {
      if (filters.startDate) url += `&startDate=${filters.startDate}`;
      if (filters.endDate) url += `&endDate=${filters.endDate}`;
    }
    return this.http.get<any[]>(url).pipe(
      catchError(err => throwError(() => new Error(`Failed to load financial trends: ${err.message}`)))
    );
  }

  /**
   * Export financial report
   */
  exportFinancialReport(farmId: string, format: 'csv' | 'pdf' | 'excel' = 'pdf', filters?: { startDate?: string; endDate?: string }): Observable<Blob> {
    let url = `${this.apiUrl}/farms/${farmId}/export?format=${format}`;
    if (filters) {
      if (filters.startDate) url += `&startDate=${filters.startDate}`;
      if (filters.endDate) url += `&endDate=${filters.endDate}`;
    }
    return this.http.get(url, { responseType: 'blob' }).pipe(
      catchError(err => throwError(() => new Error(`Failed to export financial report: ${err.message}`)))
    );
  }

  /**
   * Get budget vs actual for an operation
   */
  getBudgetVsActual(operationId: string, filters?: { startDate?: string; endDate?: string }): Observable<any> {
    let url = `${this.apiUrl}/operations/${operationId}/budget-vs-actual`;
    if (filters) {
      const params = new URLSearchParams();
      if (filters.startDate) params.append('startDate', filters.startDate);
      if (filters.endDate) params.append('endDate', filters.endDate);
      if (params.toString()) url += `?${params.toString()}`;
    }
    return this.http.get(url).pipe(
      catchError(err => throwError(() => new Error(`Failed to load budget vs actual: ${err.message}`)))
    );
  }

  /**
   * Helper: Calculate key metrics
   */
  calculateMetrics(costs: FarmCost[], revenue: FarmRevenue[]): any {
    const totalCosts = costs.reduce((sum, c) => sum + (c.amount || 0), 0);
    const totalRevenue = revenue.reduce((sum, r) => sum + (r.totalRevenue || 0), 0);
    const grossProfit = totalRevenue - totalCosts;
    const roi = totalCosts > 0 ? (grossProfit / totalCosts) * 100 : 0;
    const profitMargin = totalRevenue > 0 ? (grossProfit / totalRevenue) * 100 : 0;

    return {
      totalCosts,
      totalRevenue,
      grossProfit,
      roi,
      profitMargin,
      breakEvenRequired: totalCosts
    };
  }
}
