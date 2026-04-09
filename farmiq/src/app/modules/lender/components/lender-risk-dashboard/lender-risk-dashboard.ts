import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { LenderService } from '../../services/lender';
import { SupabaseService } from '../../../auth/services/supabase';
import { AuthRoleService } from '../../../auth/services/auth-role';
import { Subject, combineLatest } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-lender-risk-dashboard',
  imports: [CommonModule, FormsModule],
  templateUrl: './lender-risk-dashboard.html',
  styles: [`
    .lender-risk-dashboard {
      .dashboard-header {
        padding: 20px;
        border-bottom: 1px solid #e0e0e0;
        background: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

        .header-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 20px;

          h1 {
            margin: 0;
            font-size: 24px;
            font-weight: 600;
            color: #333;
          }

          .header-actions {
            display: flex;
            gap: 10px;
            align-items: center;

            button {
              display: flex;
              align-items: center;
              gap: 8px;
              padding: 10px 16px;
              border: none;
              border-radius: 6px;
              cursor: pointer;
              font-weight: 500;
              transition: all 0.2s ease;
              font-size: 14px;

              &:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
              }

              &:active {
                transform: translateY(0);
              }

              .chat-icon,
              .signout-icon {
                font-size: 18px;
              }

              .btn-text {
                @media (max-width: 768px) {
                  display: none;
                }
              }
            }

            .btn-chat {
              background-color: #4CAF50;
              color: white;

              &:hover {
                background-color: #45a049;
              }
            }

            .btn-signout {
              background-color: #f44336;
              color: white;

              &:hover {
                background-color: #da190b;
              }
            }
          }
        }
      }

      .loading-spinner {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 20px;
        text-align: center;

        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #f3f3f3;
          border-top: 4px solid #4CAF50;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 20px;
        }

        p {
          color: #666;
          font-size: 16px;
        }
      }

      @keyframes spin {
        0% {
          transform: rotate(0deg);
        }
        100% {
          transform: rotate(360deg);
        }
      }

      .error-alert {
        padding: 15px 20px;
        margin: 20px;
        background-color: #ffebee;
        color: #c62828;
        border-left: 4px solid #f44336;
        border-radius: 4px;
      }

      .dashboard-content {
        padding: 20px;
      }

      .risk-summary {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-bottom: 30px;

        .risk-card {
          padding: 20px;
          border-radius: 8px;
          color: white;
          text-align: center;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

          h3 {
            margin: 0 0 10px 0;
            font-size: 16px;
            font-weight: 600;
          }

          .risk-count {
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
          }

          .risk-percentage {
            font-size: 14px;
            opacity: 0.9;
            margin: 0;
          }

          &.high-risk {
            background: linear-gradient(135deg, #f44336 0%, #e53935 100%);
          }

          &.medium-risk {
            background: linear-gradient(135deg, #FFC107 0%, #FFA000 100%);
          }

          &.low-risk {
            background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
          }
        }
      }

      .portfolio-health {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-bottom: 30px;
        padding: 20px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

        @media (max-width: 768px) {
          grid-template-columns: 1fr;
        }

        .health-metric {
          h3 {
            margin: 0 0 15px 0;
            font-size: 16px;
            color: #333;
          }

          .health-value {
            font-size: 32px;
            font-weight: bold;
            color: #4CAF50;
            margin: 10px 0;
          }

          .health-bar {
            width: 100%;
            height: 8px;
            background-color: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 15px;

            .health-fill {
              height: 100%;
              background: linear-gradient(90deg, #4CAF50, #8BC34A);
              border-radius: 4px;
              transition: width 0.3s ease;
            }
          }
        }

        .portfolio-stats {
          display: flex;
          flex-direction: column;
          justify-content: center;
          gap: 15px;

          .stat {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;

            &:last-child {
              border-bottom: none;
            }

            .stat-label {
              color: #666;
              font-weight: 500;
            }

            .stat-value {
              font-weight: 600;
              color: #333;
            }
          }
        }
      }

      .search-filter {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 15px;
        margin-bottom: 20px;

        @media (max-width: 768px) {
          grid-template-columns: 1fr;
        }

        .search-input,
        .filter-select {
          padding: 10px 15px;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 14px;
          font-family: inherit;

          &:focus {
            outline: none;
            border-color: #4CAF50;
            box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
          }
        }

        .filter-select {
          cursor: pointer;
        }
      }

      .profiles-table {
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        overflow-x: auto;

        table {
          width: 100%;
          border-collapse: collapse;

          thead {
            background-color: #f5f5f5;
            border-bottom: 2px solid #ddd;

            th {
              padding: 15px;
              text-align: left;
              font-weight: 600;
              color: #333;
              font-size: 14px;
            }
          }

          tbody {
            tr {
              border-bottom: 1px solid #eee;
              transition: background-color 0.2s ease;

              &:hover {
                background-color: #f9f9f9;
              }

              td {
                padding: 15px;
                color: #666;
                font-size: 14px;

                &.farmer-name {
                  font-weight: 500;
                  color: #333;
                }

                &.risk-score {
                  font-weight: 600;
                  color: #333;
                }

                .risk-badge {
                  display: inline-block;
                  padding: 4px 12px;
                  border-radius: 20px;
                  color: white;
                  font-size: 12px;
                  font-weight: 600;
                }

                &.actions-col {
                  text-align: center;
                }

                .action-btn {
                  padding: 8px 16px;
                  background-color: #4CAF50;
                  color: white;
                  border: none;
                  border-radius: 4px;
                  cursor: pointer;
                  font-weight: 500;
                  transition: background-color 0.2s ease;

                  &:hover {
                    background-color: #45a049;
                  }

                  &:active {
                    transform: scale(0.98);
                  }
                }
              }
            }
          }
        }
      }
    }
  `],
})
export class LenderRiskDashboardComponent implements OnInit, OnDestroy {
  private lenderService = inject(LenderService);
  private supabaseService = inject(SupabaseService);
  private authRoleService = inject(AuthRoleService);
  private router = inject(Router);
  private destroy$ = new Subject<void>();

  riskProfiles: any[] = [];
  filteredProfiles: any[] = [];
  portfolioMetrics: any = null;
  loading = false;
  error: string | null = null;
  selectedRiskLevel = 'all';
  searchTerm = '';

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
      this.lenderService.getRiskProfiles(),
      this.lenderService.getPortfolioMetrics(),
    ])
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: ([profiles, metrics]) => {
          this.riskProfiles = profiles;
          this.portfolioMetrics = metrics;
          this.filterProfiles();
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load risk data';
          this.loading = false;
        }
      });
  }

  filterProfiles() {
    this.filteredProfiles = this.riskProfiles.filter((profile) => {
      const matchSearch = profile.farmerName.toLowerCase().includes(this.searchTerm.toLowerCase());
      const matchRisk = this.selectedRiskLevel === 'all' || profile.riskLevel === this.selectedRiskLevel;
      return matchSearch && matchRisk;
    });
  }

  onSearch() {
    this.filterProfiles();
  }

  onRiskFilterChange() {
    this.filterProfiles();
  }

  getRiskColor(riskLevel: string): string {
    const colors: { [key: string]: string } = {
      'low': '#4CAF50',
      'medium': '#FFC107',
      'high': '#F44336',
    };
    return colors[riskLevel.toLowerCase()] || '#999';
  }

  getHighRiskCount(): number {
    return this.riskProfiles.filter(p => p.riskLevel === 'high').length;
  }

  getMediumRiskCount(): number {
    return this.riskProfiles.filter(p => p.riskLevel === 'medium').length;
  }

  getLowRiskCount(): number {
    return this.riskProfiles.filter(p => p.riskLevel === 'low').length;
  }

  /**
   * Navigate to FarmGrow chatbot
   */
  goToChatbot(): void {
    this.router.navigateByUrl('/farmgrow');
  }

  /**
   * Sign out user
   */
  async signOut(): Promise<void> {
    try {
      await this.supabaseService.signOut();
      this.router.navigateByUrl('/login');
    } catch (error) {
      console.error('Error signing out:', error);
      this.error = 'Failed to sign out. Please try again.';
    }
  }
}
