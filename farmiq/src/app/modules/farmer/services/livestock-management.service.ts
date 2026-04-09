import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import { FarmLivestockUnit, LivestockHealthRecord, LivestockProductionRecord, LivestockType } from '../models/livestock-operations.models';

/**
 * LivestockManagementService
 * Manages livestock operations including units, health records, and production tracking
 */
@Injectable({
  providedIn: 'root'
})
export class LivestockManagementService {
  private apiUrl = '/api/livestock';
  private livestockUnitsSubject = new BehaviorSubject<FarmLivestockUnit[]>([]);
  public livestockUnits$ = this.livestockUnitsSubject.asObservable();

  private healthRecordsSubject = new BehaviorSubject<LivestockHealthRecord[]>([]);
  public healthRecords$ = this.healthRecordsSubject.asObservable();

  private productionRecordsSubject = new BehaviorSubject<LivestockProductionRecord[]>([]);
  public productionRecords$ = this.productionRecordsSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Get all livestock types (reference data)
   */
  getLivestockTypes(): Observable<LivestockType[]> {
    return this.http.get<LivestockType[]>(`${this.apiUrl}/types`).pipe(
      catchError(err => this.handleError('Failed to load livestock types', err))
    );
  }

  /**
   * Get livestock units for a specific farm
   */
  getFarmLivestockUnits(farmId: string): Observable<FarmLivestockUnit[]> {
    return this.http.get<FarmLivestockUnit[]>(`${this.apiUrl}/farms/${farmId}/units`).pipe(
      tap(units => {
        this.livestockUnitsSubject.next(units);
        console.log(`✅ Loaded ${units.length} livestock units for farm ${farmId}`);
      }),
      catchError(err => throwError(() => new Error(`Failed to load livestock units: ${err.message}`)))
    );
  }

  /**
   * Create a new livestock unit
   */
  createLivestockUnit(farmId: string, unit: Partial<FarmLivestockUnit>): Observable<FarmLivestockUnit> {
    return this.http.post<FarmLivestockUnit>(`${this.apiUrl}/farms/${farmId}/units`, unit).pipe(
      tap(created => {
        const current = this.livestockUnitsSubject.value;
        this.livestockUnitsSubject.next([...current, created]);
        console.log(`✅ Livestock unit created: ${created.unitName}`);
      }),
      catchError(err => throwError(() => new Error(`Failed to create livestock unit: ${err.message}`)))
    );
  }

  /**
   * Update livestock unit details
   */
  updateLivestockUnit(unitId: string, updates: Partial<FarmLivestockUnit>): Observable<FarmLivestockUnit> {
    return this.http.patch<FarmLivestockUnit>(`${this.apiUrl}/units/${unitId}`, updates).pipe(
      tap(updated => {
        const current = this.livestockUnitsSubject.value;
        const index = current.findIndex(u => u.id === unitId);
        if (index > -1) {
          current[index] = updated;
          this.livestockUnitsSubject.next([...current]);
        }
        console.log(`✅ Livestock unit updated: ${updated.unitName}`);
      }),
      catchError(err => throwError(() => new Error(`Failed to update livestock unit: ${err.message}`)))
    );
  }

  /**
   * Delete livestock unit
   */
  deleteLivestockUnit(unitId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/units/${unitId}`).pipe(
      tap(() => {
        const current = this.livestockUnitsSubject.value;
        const filtered = current.filter(u => u.id !== unitId);
        this.livestockUnitsSubject.next(filtered);
        console.log(`✅ Livestock unit deleted: ${unitId}`);
      }),
      catchError(err => throwError(() => new Error(`Failed to delete livestock unit: ${err.message}`)))
    );
  }

  /**
   * Record health event (vaccination, treatment, disease)
   */
  recordHealthEvent(unitId: string, record: Partial<LivestockHealthRecord>): Observable<LivestockHealthRecord> {
    return this.http.post<LivestockHealthRecord>(`${this.apiUrl}/units/${unitId}/health-records`, record).pipe(
      tap(created => {
        const current = this.healthRecordsSubject.value;
        this.healthRecordsSubject.next([...current, created]);
        console.log(`✅ Health record created for unit ${unitId}`);
      }),
      catchError(err => throwError(() => new Error(`Failed to record health event: ${err.message}`)))
    );
  }

  /**
   * Get health records for a livestock unit
   */
  getHealthRecords(unitId: string, filters?: { startDate?: string; endDate?: string; eventType?: string }): Observable<LivestockHealthRecord[]> {
    let url = `${this.apiUrl}/units/${unitId}/health-records`;
    if (filters) {
      const params = new URLSearchParams();
      if (filters.startDate) params.append('startDate', filters.startDate);
      if (filters.endDate) params.append('endDate', filters.endDate);
      if (filters.eventType) params.append('eventType', filters.eventType);
      if (params.toString()) url += `?${params.toString()}`;
    }
    return this.http.get<LivestockHealthRecord[]>(url).pipe(
      tap(records => this.healthRecordsSubject.next(records)),
      catchError(err => throwError(() => new Error(`Failed to load health records: ${err.message}`)))
    );
  }

  /**
   * Record production metrics (milk, eggs, weight gain)
   */
  recordProductionMetrics(unitId: string, record: Partial<LivestockProductionRecord>): Observable<LivestockProductionRecord> {
    return this.http.post<LivestockProductionRecord>(`${this.apiUrl}/units/${unitId}/production-records`, record).pipe(
      tap(created => {
        const current = this.productionRecordsSubject.value;
        this.productionRecordsSubject.next([...current, created]);
        console.log(`✅ Production record created for unit ${unitId}`);
      }),
      catchError(err => throwError(() => new Error(`Failed to record production metrics: ${err.message}`)))
    );
  }

  /**
   * Get production records for a livestock unit
   */
  getProductionRecords(unitId: string, filters?: { startDate?: string; endDate?: string; metricType?: string }): Observable<LivestockProductionRecord[]> {
    let url = `${this.apiUrl}/units/${unitId}/production-records`;
    if (filters) {
      const params = new URLSearchParams();
      if (filters.startDate) params.append('startDate', filters.startDate);
      if (filters.endDate) params.append('endDate', filters.endDate);
      if (filters.metricType) params.append('metricType', filters.metricType);
      if (params.toString()) url += `?${params.toString()}`;
    }
    return this.http.get<LivestockProductionRecord[]>(url).pipe(
      tap(records => this.productionRecordsSubject.next(records)),
      catchError(err => throwError(() => new Error(`Failed to load production records: ${err.message}`)))
    );
  }

  /**
   * Get livestock summary for a farm
   */
  getFarmLivestockSummary(farmId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/farms/${farmId}/summary`).pipe(
      catchError(err => this.handleError('Failed to load livestock summary', err))
    );
  }

  /**
   * Export livestock data for a farm
   */
  exportLivestockData(farmId: string, format: 'csv' | 'pdf' = 'csv'): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/farms/${farmId}/export?format=${format}`, { responseType: 'blob' }).pipe(
      catchError(err => this.handleError('Failed to export livestock data', err))
    );
  }

  /**
   * Helper: Error handling
   */
  private handleError(message: string, error: any) {
    console.error(message, error);
    return throwError(() => new Error(message));
  }
}
