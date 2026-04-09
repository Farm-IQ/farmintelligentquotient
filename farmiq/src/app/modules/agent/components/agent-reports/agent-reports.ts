import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AgentService } from '../../services/agent';
import { Subject, combineLatest } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-agent-reports',
  imports: [CommonModule],
  templateUrl: './agent-reports.html',
  styleUrl: './agent-reports.scss',
})
export class AgentReportsComponent implements OnInit, OnDestroy {
  private agentService = inject(AgentService);
  private destroy$ = new Subject<void>();

  performance: any = null;
  detailedReport: any = null;
  monthlyReport: any = null;
  loading = false;
  error: string | null = null;
  selectedPeriod = 'month';

  ngOnInit() {
    this.loadReportData();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadReportData() {
    this.loading = true;
    this.error = null;

    const currentMonth = new Date().toISOString().slice(0, 7); // YYYY-MM format

    combineLatest([
      this.agentService.getPerformance(),
      this.agentService.getDetailedReport(),
      this.agentService.getMonthlyPerformance(currentMonth),
    ])
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: ([perf, detailed, monthly]) => {
          this.performance = perf;
          this.detailedReport = detailed;
          this.monthlyReport = monthly;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load report data';
          this.loading = false;
        }
      });
  }

  getMetricValue(metric: string): any {
    return this.performance?.[metric] || 0;
  }

  getPerformanceClass(value: number, threshold: number): string {
    return value >= threshold ? 'good' : 'warning';
  }

  getTopMetrics(): any[] {
    return this.detailedReport?.topMetrics || [];
  }

  getMonthlyTrend(): any[] {
    return this.monthlyReport?.trend || [];
  }

  downloadReport() {
    const data = JSON.stringify({
      performance: this.performance,
      detailed: this.detailedReport,
      monthly: this.monthlyReport,
    }, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `agent-report-${new Date().toISOString()}.json`;
    link.click();
  }
}
