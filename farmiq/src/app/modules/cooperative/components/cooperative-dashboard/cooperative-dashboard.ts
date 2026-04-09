import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { CooperativeService } from '../../services/cooperative';
import { SupabaseService } from '../../../auth/services/supabase';
import { Subject, combineLatest } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-cooperative-dashboard',
  imports: [CommonModule],
  templateUrl: './cooperative-dashboard.html',
  styles: [`
    .cooperative-dashboard {
      .dashboard-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 1px solid #e5e7eb;
      }

      .dashboard-header h1 {
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        color: #1f2937;
      }

      .dashboard-header .header-actions {
        display: flex;
        gap: 12px;
        align-items: center;
      }

      .btn-chat,
      .btn-signout {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 16px;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        white-space: nowrap;
      }

      .btn-chat {
        background-color: #3b82f6;
        color: white;
      }

      .btn-chat:hover {
        background-color: #2563eb;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
      }

      .btn-chat:active {
        transform: translateY(0);
      }

      .btn-signout {
        background-color: #e5e7eb;
        color: #1f2937;
      }

      .btn-signout:hover {
        background-color: #d1d5db;
        transform: translateY(-2px);
      }

      .btn-signout:active {
        transform: translateY(0);
      }

      .chat-icon,
      .signout-icon {
        font-size: 16px;
      }

      .btn-text {
        display: inline;
      }

      @media (max-width: 640px) {
        .dashboard-header {
          flex-direction: column;
          align-items: flex-start;
          gap: 12px;
        }

        .btn-chat .btn-text,
        .btn-signout .btn-text {
          display: none;
        }
      }
    }
  `],
})
export class CooperativeDashboardComponent implements OnInit, OnDestroy {
  private cooperativeService = inject(CooperativeService);
  private supabaseService = inject(SupabaseService);
  private router = inject(Router);
  private destroy$ = new Subject<void>();

  cooperativeData: any = null;
  members: any[] = [];
  insights: any = null;
  loading = false;
  error: string | null = null;

  ngOnInit() {
    this.loadDashboardData();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadDashboardData() {
    this.loading = true;
    this.error = null;

    combineLatest([
      this.cooperativeService.getCooperativeData(),
      this.cooperativeService.getMembers(),
      this.cooperativeService.getInsights(),
    ])
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: ([data, members, insights]) => {
          this.cooperativeData = data;
          this.members = members;
          this.insights = insights;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load cooperative data';
          this.loading = false;
        }
      });
  }

  refreshData() {
    this.loadDashboardData();
  }

  getRiskColor(riskLevel: string): string {
    const colors: { [key: string]: string } = {
      'low': '#4CAF50',
      'medium': '#FFC107',
      'high': '#F44336',
    };
    return colors[riskLevel.toLowerCase()] || '#999';
  }

  getMemberCount(): number {
    return this.members?.length || 0;
  }

  getAverageScore(): number {
    if (!this.members || this.members.length === 0) return 0;
    const total = this.members.reduce((sum, m) => sum + (m.fiqScore || 0), 0);
    return Math.round(total / this.members.length);
  }

  goToChatbot(): void {
    this.router.navigateByUrl('/farmgrow');
  }

  async signOut(): Promise<void> {
    try {
      console.log('🚪 Cooperative signing out...');
      await this.supabaseService.signOut();
      console.log('✅ Cooperative logged out successfully');
      // Navigate to login after logout
      this.router.navigate(['/login']);
    } catch (error) {
      console.error('❌ Logout error:', error);
      // Even if there's an error, navigate to login
      this.router.navigate(['/login']);
    }
  }
}
