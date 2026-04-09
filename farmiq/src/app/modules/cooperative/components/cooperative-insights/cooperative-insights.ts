import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CooperativeService } from '../../services/cooperative';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-cooperative-insights',
  imports: [CommonModule],
  templateUrl: './cooperative-insights.html',
  styleUrl: './cooperative-insights.scss',
})
export class CooperativeInsightsComponent implements OnInit, OnDestroy {
  private cooperativeService = inject(CooperativeService);
  private destroy$ = new Subject<void>();

  insights: any = null;
  loading = false;
  error: string | null = null;
  selectedMetric = 'revenue';

  ngOnInit() {
    this.loadInsights();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadInsights() {
    this.loading = true;
    this.error = null;

    this.cooperativeService.getInsights()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.insights = data;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load insights';
          this.loading = false;
        }
      });
  }

  getMetricValue(metric: string): any {
    if (!this.insights) return null;
    return this.insights[metric] || 0;
  }

  getTopPerformers(): any[] {
    return this.insights?.topPerformers || [];
  }

  getTrendClass(trend: number): string {
    return trend > 0 ? 'positive' : 'negative';
  }

  getTrendIcon(trend: number): string {
    return trend > 0 ? '↑' : '↓';
  }

  getMarketTrend(): string {
    return this.insights?.marketTrend || 'stable';
  }

  getMarketTrendColor(): string {
    const trend = this.getMarketTrend();
    const colors: { [key: string]: string } = {
      'bullish': '#4CAF50',
      'stable': '#FFC107',
      'bearish': '#F44336',
    };
    return colors[trend.toLowerCase()] || '#999';
  }
}
