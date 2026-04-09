/**
 * Worker Performance Service
 * Handles performance evaluations, ratings, and feedback
 */

import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';

export interface PerformanceRating {
  category: 'quality' | 'productivity' | 'punctuality' | 'teamwork' | 'safety' | 'communication' | 'reliability';
  score: number; // 1-5
  weight: number; // 0-100, percentage
  comment?: string;
}

export interface PerformanceEvaluation {
  id: string;
  workerId: string;
  evaluatedBy: string;
  evaluationDate: string;
  period: string; // YYYY-MM or YYYY-Q1, etc
  ratings: PerformanceRating[];
  overallScore: number; // calculated average
  strengths: string[];
  areasForImprovement: string[];
  goals: string[];
  feedback: string;
  status: 'draft' | 'submitted' | 'reviewed';
  reviewedBy?: string;
  reviewDate?: string;
  salary_adjustment?: number; // percentage
}

export interface PerformanceMetrics {
  workerId: string;
  currentScore: number; // overall score out of 5
  trend: 'improving' | 'stable' | 'declining';
  evaluationCount: number;
  lastEvaluationDate: string;
  avgScores: Record<string, number>;
  riskStatus: 'low' | 'medium' | 'high'; // for performance improvement plans
}

@Injectable({ providedIn: 'root' })
export class WorkerPerformanceService {
  private apiUrl = environment.apiUrl;
  private supabaseUrl = `${environment.supabase.url}/rest/v1`;

  // ========== STATE ==========
  evaluations = signal<PerformanceEvaluation[]>([]);
  currentEvaluation = signal<PerformanceEvaluation | null>(null);
  metrics = signal<PerformanceMetrics | null>(null);
  loading = signal<boolean>(false);
  error = signal<string | null>(null);

  // ========== COMPUTED ==========
  latestEvaluation = computed(() => {
    const evals = this.evaluations();
    return evals.length > 0 ? evals[0] : null;
  });

  performanceTrend = computed(() => {
    const metrics = this.metrics();
    return metrics?.trend || 'stable';
  });

  averageScore = computed(() => {
    const metrics = this.metrics();
    return metrics?.currentScore || 0;
  });

  highPerformers = computed(() => {
    const metrics = this.metrics();
    return metrics && metrics.currentScore >= 4 ? true : false;
  });

  needsImprovement = computed(() => {
    const metrics = this.metrics();
    return metrics && metrics.riskStatus === 'high' ? true : false;
  });

  constructor(private http: HttpClient) {}

  /**
   * Get evaluations for a worker
   */
  getWorkerEvaluations(workerId: string, limit: number = 12): Observable<PerformanceEvaluation[]> {
    this.loading.set(true);
    return this.http.get<PerformanceEvaluation[]>(
      `${this.supabaseUrl}/performance_evaluations?worker_id=eq.${workerId}&order=evaluation_date.desc&limit=${limit}`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((evals: PerformanceEvaluation[]) => {
        this.evaluations.set(evals);
        this.loading.set(false);
      }),
      catchError((err) => this.handleError('Failed to fetch evaluations', err))
    );
  }

  /**
   * Create a new performance evaluation
   */
  createEvaluation(
    workerId: string,
    evaluatedBy: string,
    evaluation: Omit<PerformanceEvaluation, 'id' | 'overallScore'>
  ): Observable<PerformanceEvaluation> {
    // LOGIC: Calculate overall score (weighted average)
    const overallScore = this.calculateOverallScore(evaluation.ratings);

    const payload = {
      worker_id: workerId,
      evaluated_by: evaluatedBy,
      evaluation_date: evaluation.evaluationDate,
      period: evaluation.period,
      ratings: evaluation.ratings,
      overall_score: overallScore,
      strengths: evaluation.strengths,
      areas_for_improvement: evaluation.areasForImprovement,
      goals: evaluation.goals,
      feedback: evaluation.feedback,
      status: 'draft'
    };

    return this.http.post<PerformanceEvaluation>(
      `${this.supabaseUrl}/performance_evaluations`,
      payload,
      { headers: this.getHeaders() }
    ).pipe(
      tap((newEval: PerformanceEvaluation) => {
        const updated = [...this.evaluations(), newEval];
        this.evaluations.set(updated);
      }),
      catchError((err) => this.handleError('Failed to create evaluation', err))
    );
  }

  /**
   * LOGIC: Calculate overall performance score
   * Formula: Weighted average of all ratings
   */
  private calculateOverallScore(ratings: PerformanceRating[]): number {
    if (ratings.length === 0) return 0;

    let totalWeightedScore = 0;
    let totalWeight = 0;

    ratings.forEach(rating => {
      totalWeightedScore += (rating.score * rating.weight);
      totalWeight += rating.weight;
    });

    const score = totalWeight > 0 
      ? totalWeightedScore / totalWeight 
      : 0;

    return Math.round(score * 100) / 100; // Round to 2 decimals
  }

  /**
   * Submit evaluation for review
   */
  submitEvaluation(evaluationId: string): Observable<PerformanceEvaluation> {
    return this.http.patch<PerformanceEvaluation>(
      `${this.supabaseUrl}/performance_evaluations?id=eq.${evaluationId}`,
      { status: 'submitted' },
      { headers: this.getHeaders() }
    ).pipe(
      catchError((err) => this.handleError('Failed to submit evaluation', err))
    );
  }

  /**
   * Review evaluation (manager only)
   */
  reviewEvaluation(
    evaluationId: string,
    reviewedBy: string,
    salaryAdjustment?: number
  ): Observable<PerformanceEvaluation> {
    const payload = {
      status: 'reviewed',
      reviewed_by: reviewedBy,
      review_date: new Date().toISOString(),
      ...(salaryAdjustment && { salary_adjustment: salaryAdjustment })
    };

    return this.http.patch<PerformanceEvaluation>(
      `${this.supabaseUrl}/performance_evaluations?id=eq.${evaluationId}`,
      payload,
      { headers: this.getHeaders() }
    ).pipe(
      catchError((err) => this.handleError('Failed to review evaluation', err))
    );
  }

  /**
   * Get performance metrics for a worker
   */
  getPerformanceMetrics(workerId: string): Observable<PerformanceMetrics> {
    return this.http.get<PerformanceMetrics>(
      `${this.apiUrl}/workers/${workerId}/performance-metrics`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((metrics: PerformanceMetrics) => {
        this.metrics.set(metrics);
      }),
      catchError((err) => this.handleError('Failed to fetch metrics', err))
    );
  }

  /**
   * LOGIC: Determine performance improvement plan need
   * Returns true if score < 2 or declining trend for 2+ consecutive evaluations
   */
  needsPerformanceImprovementPlan(workerId: string): Observable<boolean> {
    return this.getWorkerEvaluations(workerId, 3).pipe(
      switchMap((evals) => {
        if (evals.length === 0) return of(false);

        const recentScore = evals[0].overallScore;
        
        // Immediate PIP if score below 2
        if (recentScore < 2) {
          return of(true);
        }

        // PIP if declining trend for 2+ evaluations
        if (evals.length >= 2) {
          const previousScore = evals[1].overallScore;
          if (evals.length >= 3) {
            const oldestScore = evals[2].overallScore;
            if (previousScore < recentScore && recentScore < oldestScore) {
              return of(true);
            }
          } else if (previousScore > recentScore) {
            return of(true); // Declining trend
          }
        }

        return of(false);
      }),
      catchError(() => of(false))
    );
  }

  /**
   * Get high performers for recognition/rewards
   */
  getHighPerformers(farmId: string, threshold: number = 4.0): Observable<PerformanceMetrics[]> {
    return this.http.get<PerformanceMetrics[]>(
      `${this.apiUrl}/farms/${farmId}/high-performers?threshold=${threshold}`,
      { headers: this.getHeaders() }
    ).pipe(
      catchError((err) => this.handleError('Failed to fetch high performers', err))
    );
  }

  /**
   * Generate performance report for a period
   */
  generatePerformanceReport(farmId: string, period: string): Observable<Blob> {
    return this.http.get(
      `${this.apiUrl}/farms/${farmId}/performance-report?period=${period}&format=pdf`,
      { responseType: 'blob', headers: this.getHeaders() }
    ).pipe(
      catchError((err) => this.handleError('Failed to generate report', err))
    );
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

// Add missing imports
import { switchMap } from 'rxjs/operators';
import { of } from 'rxjs';
