import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LenderService } from '../../services/lender';
import { Subject, combineLatest } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-lender-portfolio-monitoring',
  imports: [CommonModule, FormsModule],
  templateUrl: './lender-portfolio-monitoring.html',
  styleUrl: './lender-portfolio-monitoring.scss',
})
export class LenderPortfolioMonitoringComponent implements OnInit, OnDestroy {
  private lenderService = inject(LenderService);
  private destroy$ = new Subject<void>();

  portfolioMetrics: any = null;
  loansByStatus: any[] = [];
  loading = false;
  error: string | null = null;
  selectedLoanId: string | null = null;
  loanDetails: any = null;

  ngOnInit() {
    this.loadPortfolioData();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadPortfolioData() {
    this.loading = true;
    this.error = null;

    combineLatest([
      this.lenderService.getPortfolioMetrics(),
      this.lenderService.getAllApplications(),
    ])
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: ([metrics, loans]) => {
          this.portfolioMetrics = metrics;
          this.loansByStatus = loans;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load portfolio data';
          this.loading = false;
        }
      });
  }

  selectLoan(loanId: string) {
    this.selectedLoanId = loanId;
    this.loadLoanDetails(loanId);
  }

  loadLoanDetails(loanId: string) {
    this.lenderService.getLoanApplication(loanId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (details) => {
          this.loanDetails = details;
        },
        error: (err) => {
          this.error = 'Failed to load loan details';
        }
      });
  }

  monitorLoan(loanId: string) {
    this.lenderService.monitorLoan(loanId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (result) => {
          this.loadPortfolioData();
        },
        error: (err) => {
          this.error = 'Failed to update loan monitoring';
        }
      });
  }

  getStatusColor(status: string): string {
    const colors: { [key: string]: string } = {
      'active': '#4CAF50',
      'pending': '#FFC107',
      'defaulted': '#F44336',
      'paid': '#2196F3',
    };
    return colors[status.toLowerCase()] || '#999';
  }

  getHealthPercentage(): number {
    if (!this.portfolioMetrics) return 0;
    const healthyLoans = this.portfolioMetrics.activeLoans - this.portfolioMetrics.defaultedLoans;
    return (healthyLoans / this.portfolioMetrics.totalLoans) * 100;
  }

  getDefaultRate(): number {
    if (!this.portfolioMetrics) return 0;
    return (this.portfolioMetrics.defaultedLoans / this.portfolioMetrics.totalLoans) * 100;
  }
}
