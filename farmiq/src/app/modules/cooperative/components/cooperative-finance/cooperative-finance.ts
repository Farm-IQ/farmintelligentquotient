import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CooperativeService } from '../../services/cooperative';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-cooperative-finance',
  imports: [CommonModule],
  templateUrl: './cooperative-finance.html',
  styleUrl: './cooperative-finance.scss',
})
export class CooperativeFinanceComponent implements OnInit, OnDestroy {
  private cooperativeService = inject(CooperativeService);
  private destroy$ = new Subject<void>();

  financialOverview: any = null;
  loading = false;
  error: string | null = null;
  selectedPeriod = 'month';

  ngOnInit() {
    this.loadFinancialData();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadFinancialData() {
    this.loading = true;
    this.error = null;

    this.cooperativeService.getFinancialOverview()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.financialOverview = data;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load financial data';
          this.loading = false;
        }
      });
  }

  getRevenueData(): any[] {
    if (!this.financialOverview) return [];
    return this.financialOverview.revenueByMonth || [];
  }

  getExpenseData(): any[] {
    if (!this.financialOverview) return [];
    return this.financialOverview.expensesByMonth || [];
  }

  getTotalRevenue(): number {
    if (!this.financialOverview) return 0;
    return this.financialOverview.totalRevenue || 0;
  }

  getTotalExpenses(): number {
    if (!this.financialOverview) return 0;
    return this.financialOverview.totalExpenses || 0;
  }

  getNetProfit(): number {
    return this.getTotalRevenue() - this.getTotalExpenses();
  }

  getProfitMargin(): number {
    const revenue = this.getTotalRevenue();
    if (revenue === 0) return 0;
    return (this.getNetProfit() / revenue) * 100;
  }

  getTopExpenseCategories(): any[] {
    return this.financialOverview?.topExpenseCategories || [];
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  }
}
