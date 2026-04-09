import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AdminService } from '../../services/admin';
import { SupabaseService } from '../../../auth/services/supabase';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './admin-dashboard.html',
  styles: [`
    .admin-dashboard {
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
export class AdminDashboardComponent implements OnInit, OnDestroy {
  private adminService = inject(AdminService);
  private supabaseService = inject(SupabaseService);
  private router = inject(Router);
  private destroy$ = new Subject<void>();

  systemMetrics: any = {
    totalUsers: 0,
    activeUsers: 0,
    totalFarms: 0,
    totalLoans: 0,
    platformRevenue: 0,
    systemHealth: 0,
    uptime: '99.9%',
    avgResponseTime: '245ms'
  };

  userStatistics: any = {
    farmers: 0,
    cooperatives: 0,
    lenders: 0,
    agents: 0,
    admins: 0
  };

  recentActivities: any[] = [];
  alertsList: any[] = [];
  loading = false;
  error = '';

  ngOnInit() {
    this.loadDashboardData();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadDashboardData() {
    this.loading = true;
    this.adminService.getSystemMetrics()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (metrics) => {
          this.systemMetrics = metrics;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load system metrics';
          this.loading = false;
        }
      });
  }

  refreshData() {
    this.loadDashboardData();
  }

  getHealthColor(health: number): string {
    if (health >= 90) return '#4CAF50';
    if (health >= 70) return '#FFC107';
    return '#f44336';
  }

  getStatusClass(status: string): string {
    return status === 'Active' ? 'status-active' : 'status-inactive';
  }

  goToChatbot(): void {
    this.router.navigateByUrl('/farmgrow');
  }

  async signOut(): Promise<void> {
    try {
      console.log('🚪 Admin signing out...');
      await this.supabaseService.signOut();
      console.log('✅ Admin logged out successfully');
      // Navigate to login after logout
      this.router.navigate(['/login']);
    } catch (error) {
      console.error('❌ Logout error:', error);
      // Even if there's an error, navigate to login
      this.router.navigate(['/login']);
    }
  }
}
