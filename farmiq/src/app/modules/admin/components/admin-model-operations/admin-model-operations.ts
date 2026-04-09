import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AdminService } from '../../services/admin';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-admin-model-operations',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './admin-model-operations.html',
  styleUrl: './admin-model-operations.scss',
})
export class AdminModelOperationsComponent implements OnInit, OnDestroy {
  private adminService = inject(AdminService);
  private destroy$ = new Subject<void>();

  modelMetrics: any = {
    accuracy: 0,
    precision: 0,
    recall: 0,
    f1Score: 0,
    lastTrainingDate: new Date(),
    modelVersion: '2.1.0',
    predictions24h: 0,
    avgInferenceTime: '125ms'
  };

  trainingHistory: any[] = [];
  selectedModel: any = null;
  loading = false;
  training = false;
  error = '';
  successMessage = '';

  ngOnInit() {
    this.loadModelMetrics();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadModelMetrics() {
    this.loading = true;
    this.adminService.getModelMetrics()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (metrics) => {
          this.modelMetrics = metrics;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load model metrics';
          this.loading = false;
        }
      });
  }

  retrainModel() {
    this.training = true;
    this.adminService.retrainModel()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (result) => {
          this.successMessage = 'Model retraining completed';
          this.loadModelMetrics();
          this.getTrainingHistory();
          this.training = false;
        },
        error: (err) => {
          this.error = 'Training failed';
          this.training = false;
        }
      });
  }

  getTrainingHistory() {
    this.adminService.getTrainingHistory()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (history) => {
          this.trainingHistory = history;
        },
        error: (err) => this.error = 'Failed to load training history'
      });
  }

  getMetricPercentage(metric: string): number {
    const metrics: any = this.modelMetrics;
    return metrics[metric] * 100 || 0;
  }

  getMetricColor(metric: string): string {
    const value = this.getMetricPercentage(metric) / 100;
    if (value >= 0.9) return '#4CAF50';
    if (value >= 0.8) return '#FFC107';
    return '#f44336';
  }

  getStatusColor(status: string): string {
    switch (status?.toLowerCase()) {
      case 'completed': return '#4CAF50';
      case 'in progress': return '#2196F3';
      case 'failed': return '#f44336';
      default: return '#999';
    }
  }
}
