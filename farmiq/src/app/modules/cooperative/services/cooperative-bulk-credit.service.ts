import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import {
  BulkScoringResult,
  BulkScoringDetailedResult,
  CooperativeMember,
  BulkScoringError,
  CooperativeBulkScoringRequest,
} from '../models/cooperative.model';

@Injectable({
  providedIn: 'root',
})
export class CooperativeBulkCreditService {
  private apiUrl = '/api/cooperatives';

  // Signals for bulk scoring state
  isScoringSignal = signal<boolean>(false);
  bulkResultSignal = signal<BulkScoringDetailedResult | null>(null);
  scoringProgressSignal = signal<number>(0);

  // BehaviorSubjects for backward compatibility
  private isScoringSubject = new BehaviorSubject<boolean>(false);
  private bulkResultSubject = new BehaviorSubject<BulkScoringDetailedResult | null>(null);

  public isScoring$ = this.isScoringSubject.asObservable();
  public bulkResult$ = this.bulkResultSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Score multiple cooperative members in bulk
   * FIXED: Returns Observable<BulkScoringDetailedResult> with processedCount
   */
  scoreMembers(
    request: CooperativeBulkScoringRequest
  ): Observable<BulkScoringDetailedResult> {
    this.isScoringSignal.set(true);
    this.isScoringSubject.next(true);

    return this.http
      .post<BulkScoringDetailedResult>(
        `${this.apiUrl}/${request.cooperativeId}/bulk-score`,
        request
      )
      .pipe(
        tap((result) => {
          this.bulkResultSignal.set(result);
          this.bulkResultSubject.next(result);
          this.isScoringSignal.set(false);
          this.isScoringSubject.next(false);
        }),
        catchError((error) => {
          this.isScoringSignal.set(false);
          this.isScoringSubject.next(false);
          console.error('Bulk scoring error:', error);
          throw error;
        })
      );
  }

  /**
   * Score individual member
   */
  scoreMember(cooperativeId: string, memberId: string): Observable<BulkScoringResult> {
    return this.http.post<BulkScoringResult>(
      `${this.apiUrl}/${cooperativeId}/score-member`,
      { memberId }
    );
  }

  /**
   * Get scoring history for cooperative
   */
  getScoringHistory(
    cooperativeId: string
  ): Observable<BulkScoringDetailedResult[]> {
    return this.http.get<BulkScoringDetailedResult[]>(
      `${this.apiUrl}/${cooperativeId}/scoring-history`
    );
  }

  /**
   * Cancel ongoing bulk scoring
   */
  cancelBulkScoring(cooperativeId: string): Observable<{ success: boolean }> {
    return this.http.post<{ success: boolean }>(
      `${this.apiUrl}/${cooperativeId}/cancel-scoring`,
      {}
    );
  }

  /**
   * Get bulk scoring result details
   */
  getBulkScoringDetails(
    cooperativeId: string,
    scoringId: string
  ): Observable<BulkScoringDetailedResult> {
    return this.http.get<BulkScoringDetailedResult>(
      `${this.apiUrl}/${cooperativeId}/scoring/${scoringId}`
    );
  }

  /**
   * Get current bulk scoring state
   */
  getCurrentBulkResult(): BulkScoringDetailedResult | null {
    return this.bulkResultSignal();
  }

  /**
   * Check if currently scoring
   */
  isCurrentlyScoring(): boolean {
    return this.isScoringSignal();
  }

  /**
   * Clear bulk result
   */
  clearBulkResult(): void {
    this.bulkResultSignal.set(null);
    this.bulkResultSubject.next(null);
  }
}
