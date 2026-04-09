/**
 * Worker Performance Tracker Component
 * Track and evaluate worker performance over time
 */

import { Component, Input, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkerManagementService } from '../../../farmer/services/worker-management.service';
import { FarmWorker, WorkerPerformance } from '../../models/worker-profile.models';

@Component({
  selector: 'app-worker-performance-tracker',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="performance-tracker">
      <h3>Performance Evaluations</h3>
      
      <div class="performance-stats">
        <div class="stat-box">
          <label>Average Score</label>
          <div class="score">{{ averageScore.toFixed(1) }}/100</div>
        </div>
        <div class="stat-box">
          <label>Total Reviews</label>
          <div class="score">{{ performanceHistory.length }}</div>
        </div>
        <div class="stat-box">
          <label>Latest Review</label>
          <div class="score">{{ latestReviewDate | date: 'MMM d, y' }}</div>
        </div>
      </div>

      <div class="performance-list">
        <div *ngIf="performanceHistory.length === 0" class="empty-state">
          No performance reviews yet
        </div>
        <div *ngFor="let review of performanceHistory" class="performance-card">
          <div class="review-header">
            <div class="review-date">Recent Review</div>
            <div class="review-score" [ngClass]="'score-' + getScoreLevel(review.score || 0)">
              {{ review.score }}/100
            </div>
          </div>
          <div class="review-details">
            <div class="detail">
              <strong>Reviewer:</strong> Performance Manager
            </div>
            <div class="detail">
              <strong>Category:</strong> General Performance
            </div>
            <div class="detail" *ngIf="review.comments">
              <strong>Comments:</strong> {{ review.comments }}
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .performance-tracker {
      padding: 0;
    }

    h3 {
      margin-top: 0;
      margin-bottom: 15px;
      color: #333;
    }

    .performance-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 15px;
      margin-bottom: 20px;
    }

    .stat-box {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 15px;
      border-radius: 8px;
      text-align: center;
    }

    .stat-box label {
      font-size: 12px;
      text-transform: uppercase;
      opacity: 0.9;
      display: block;
      margin-bottom: 8px;
    }

    .score {
      font-size: 24px;
      font-weight: bold;
    }

    .performance-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .empty-state {
      text-align: center;
      padding: 40px;
      color: #999;
      background: #f5f5f5;
      border-radius: 4px;
    }

    .performance-card {
      background: #f9f9f9;
      border: 1px solid #e0e0e0;
      border-radius: 6px;
      padding: 12px;
    }

    .review-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 10px;
    }

    .review-date {
      font-weight: 500;
      color: #333;
    }

    .review-score {
      padding: 4px 8px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 14px;
    }

    .review-score.score-excellent {
      background: #e8f5e9;
      color: #4CAF50;
    }

    .review-score.score-good {
      background: #e3f2fd;
      color: #1976d2;
    }

    .review-score.score-average {
      background: #fff3e0;
      color: #ff9800;
    }

    .review-score.score-poor {
      background: #ffebee;
      color: #f44336;
    }

    .review-details {
      font-size: 13px;
      color: #666;
    }

    .detail {
      margin: 5px 0;
    }

    .detail strong {
      color: #333;
    }
  `]
})
export class WorkerPerformanceTrackerComponent implements OnInit {
  @Input() selectedWorker: FarmWorker | null = null;

  private workerService = inject(WorkerManagementService);

  performanceHistory: WorkerPerformance[] = [];
  averageScore = 0;
  latestReviewDate = new Date();

  ngOnInit(): void {
    this.loadPerformanceData();
  }

  private loadPerformanceData(): void {
    if (!this.selectedWorker) return;

    this.workerService.getPerformanceHistory(this.selectedWorker.id)
      .then(history => {
        this.performanceHistory = history.sort((a, b) => 
          new Date(b.evaluation_date).getTime() - new Date(a.evaluation_date).getTime()
        );
        this.calculateAverageScore();
        if (this.performanceHistory.length > 0) {
          this.latestReviewDate = new Date(this.performanceHistory[0].evaluation_date);
        }
      })
      .catch(err => console.error('Failed to load performance:', err));
  }

  private calculateAverageScore(): void {
    if (this.performanceHistory.length === 0) {
      this.averageScore = 0;
      return;
    }
    const sum = this.performanceHistory.reduce((acc, review) => acc + (review.score || 0), 0);
    this.averageScore = sum / this.performanceHistory.length;
  }

  getScoreLevel(score: number): string {
    if (score >= 85) return 'excellent';
    if (score >= 75) return 'good';
    if (score >= 65) return 'average';
    return 'poor';
  }
}
