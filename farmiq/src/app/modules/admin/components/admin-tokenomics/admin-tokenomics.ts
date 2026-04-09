import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AdminService } from '../../services/admin';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-admin-tokenomics',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './admin-tokenomics.html',
  styleUrl: './admin-tokenomics.scss',
})
export class AdminTokenomicsComponent implements OnInit, OnDestroy {
  private adminService = inject(AdminService);
  private destroy$ = new Subject<void>();

  tokenomics: any = {
    totalSupply: 1000000000,
    circulatingSupply: 500000000,
    marketCap: 50000000,
    tokenPrice: 0.05,
    stakingRewards: 0,
    totalStaked: 0,
    apy: 0.12,
    holders: 0
  };

  tokenDistribution: Array<{ category: string; percentage: number }> = [];
  stakingInfo: any = {};
  loading = false;
  error = '';

  ngOnInit() {
    this.loadTokenomics();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadTokenomics() {
    this.loading = true;
    this.adminService.getTokenomics()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (tokenomics) => {
          this.tokenomics = tokenomics;
          this.getTokenDistribution();
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load tokenomics';
          this.loading = false;
        }
      });
  }

  getTokenDistribution() {
    this.adminService.getTokenDistribution()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (distribution: any) => {
          this.tokenDistribution = Array.isArray(distribution) 
            ? distribution 
            : Object.entries(distribution).map(([category, percentage]) => ({ category, percentage: percentage as number }));
        },
        error: (err) => this.error = 'Failed to load token distribution'
      });
  }

  getCirculationPercentage(): number {
    return (this.tokenomics.circulatingSupply / this.tokenomics.totalSupply) * 100;
  }

  getStakingPercentage(): number {
    return (this.tokenomics.totalStaked / this.tokenomics.circulatingSupply) * 100;
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  }
}
