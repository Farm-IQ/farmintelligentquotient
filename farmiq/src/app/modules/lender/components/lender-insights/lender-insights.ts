import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LenderService } from '../../services/lender';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-lender-insights',
  imports: [CommonModule, FormsModule],
  templateUrl: './lender-insights.html',
  styleUrl: './lender-insights.scss',
})
export class LenderInsightsComponent implements OnInit, OnDestroy {
  private lenderService = inject(LenderService);
  private destroy$ = new Subject<void>();

  marketInsights: any = null;
  loading = false;
  error: string | null = null;

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

    this.lenderService.getMarketInsights()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.marketInsights = data;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load insights';
          this.loading = false;
        }
      });
  }

  getTrendIcon(value: number): string {
    return value > 0 ? '↑' : '↓';
  }

  getTrendClass(value: number): string {
    return value > 0 ? 'positive' : 'negative';
  }

  getSectorTrends(): any[] {
    return this.marketInsights?.sectorTrends || [];
  }

  getCropOutlook(): any[] {
    return this.marketInsights?.cropOutlook || [];
  }

  getRecommendations(): any[] {
    return this.marketInsights?.recommendations || [];
  }

  getRiskFactors(): any[] {
    return this.marketInsights?.riskFactors || [];
  }
}
