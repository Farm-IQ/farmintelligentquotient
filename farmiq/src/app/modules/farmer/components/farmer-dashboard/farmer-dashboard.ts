import { Component, OnInit, OnDestroy, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { FarmerDataService } from '../../services/farmer-data.service';
import { FarmerAnalyticsService } from '../../services/farmer-analytics.service';
import { FarmerCreditService } from '../../services/farmer-credit.service';

interface FarmProfile {
  id: string;
  first_name: string;
  last_name: string;
  farm_name: string;
  location: string;
  farm_size: number;
  phone: string;
}

interface FarmData {
  id: string;
  user_id: string;
  farm_name: string;
  location: string;
  farm_size: number;
  current_crop: string;
  planting_date: string;
  expected_harvest_date: string;
  soil_health: number;
  water_availability: number;
  estimated_yield: number;
  crop_stage: string;
}

interface Analytics {
  yieldMetrics: {
    current_season: number;
    last_season: number;
    average: number;
  };
  weatherImpact: number;
  soilHealth: number;
  waterUsage: number;
  recommendations: string[];
}

interface QuickStat {
  title: string;
  value: string;
  icon: string;
  subtext?: string;
  status?: 'good' | 'fair' | 'poor' | 'critical';
  trend?: 'up' | 'down' | 'stable';
  color: string;
}

interface Alert {
  type: 'info' | 'warning' | 'danger' | 'success' | 'critical';
  title: string;
  message: string;
  icon: string;
  action?: string;
}

@Component({
  selector: 'app-farmer-dashboard',
  standalone: true,
  imports: [CommonModule, IonicModule],
  templateUrl: './farmer-dashboard.html',
  styleUrls: ['./farmer-dashboard.scss']
})
export class FarmerDashboardComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  // Constructor dependency injection for proper initialization
  constructor(
    private farmerDataService: FarmerDataService,
    private farmerAnalyticsService: FarmerAnalyticsService,
    private farmerCreditService: FarmerCreditService
  ) {}

  // ========== STATE FROM SERVICES ==========
  farmData = computed(() => this.farmerDataService.farmData());
  analytics = computed(() => this.farmerAnalyticsService.analytics());
  creditScore = computed(() => this.farmerCreditService.creditScore());
  loading = computed(() => this.farmerDataService.loading());
  error = computed(() => this.farmerDataService.error());

  // Dashboard cards
  quickStats = signal<QuickStat[]>([]);
  recentActivities = signal<string[]>([]);
  alertsNotifications = signal<Alert[]>([]);

  // UI state
  selectedTab = signal<'overview' | 'activities' | 'alerts'>('overview');
  refreshing = signal<boolean>(false);

  // Math for template access
  Math = Math;

  ngOnInit(): void {
    this.loadDashboardData();
    this.setupAutoRefresh();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load all dashboard data
   */
  private loadDashboardData(): void {
    const farmiqId = sessionStorage.getItem('farmiq_id');
    if (!farmiqId) return;

    // Load data in parallel
    this.farmerDataService.refreshData();
    this.farmerCreditService.getCreditScore(farmiqId).pipe(takeUntil(this.destroy$)).subscribe();
    
    const profile = this.farmerDataService.farmerProfile();
    if (profile?.id) {
      this.farmerAnalyticsService.getAnalytics(profile.id).pipe(takeUntil(this.destroy$)).subscribe();
    }

    this.updateQuickStats();
    this.generateAlerts();
  }

  /**
   * LOGIC: Calculate quick statistics from current data
   */
  private updateQuickStats(): void {
    const stats: QuickStat[] = [];
    const farm = this.farmData();
    const analytics = this.analytics();
    const credit = this.creditScore();

    if (farm) {
      stats.push({
        title: 'Farm Size',
        value: `${farm.farm_size_acres} acres`,
        icon: '🌾',
        trend: 'stable',
        color: 'primary'
      });

      stats.push({
        title: 'Crop Stage',
        value: farm.crop_stage.toUpperCase(),
        icon: '🌱',
        subtext: `${this.farmerDataService.cropStageProgress()}% complete`,
        color: 'success'
      });

      stats.push({
        title: 'Days to Harvest',
        value: `${this.farmerDataService.daysToHarvest()} days`,
        icon: '📅',
        subtext: farm.expected_harvest_date,
        color: 'warning'
      });

      stats.push({
        title: 'Soil Health',
        value: `${farm.soil_health}%`,
        icon: '🌍',
        status: farm.soil_health > 70 ? 'good' : farm.soil_health > 50 ? 'fair' : 'poor',
        color: this.getHealthColor(farm.soil_health)
      });

      stats.push({
        title: 'Water Availability',
        value: `${farm.water_availability}%`,
        icon: '💧',
        status: farm.water_availability > 60 ? 'good' : farm.water_availability > 40 ? 'fair' : 'critical',
        color: this.getHealthColor(farm.water_availability)
      });
    }

    if (analytics) {
      const yieldTrend = analytics.yieldMetrics.percentChange > 0 ? 'up' : 'down';
      stats.push({
        title: 'Yield Trend',
        value: `${analytics.yieldMetrics.percentChange > 0 ? '+' : ''}${analytics.yieldMetrics.percentChange}%`,
        icon: '📈',
        trend: yieldTrend,
        color: yieldTrend === 'up' ? 'success' : 'danger'
      });
    }

    if (credit) {
      stats.push({
        title: 'Credit Score',
        value: credit.score.toString(),
        icon: '💳',
        subtext: this.getCreditRating(credit.score),
        color: this.getCreditColor(credit.score)
      });
    }

    this.quickStats.set(stats);
  }

  /**
   * LOGIC: Generate alerts and notifications
   */
  private generateAlerts(): void {
    const alerts: Alert[] = [];
    const farm = this.farmData();
    const analytics = this.analytics();

    if (farm) {
      // Water availability alert
      if (farm.water_availability < 40) {
        alerts.push({
          type: 'critical',
          title: 'Low Water Availability',
          message: `Water availability at ${farm.water_availability}%. Increase irrigation immediately.`,
          icon: '⚠️',
          action: 'View Farm'
        });
      }

      // Soil health alert
      if (farm.soil_health < 50) {
        alerts.push({
          type: 'warning',
          title: 'Soil Health Declining',
          message: `Soil health at ${farm.soil_health}%. Apply nutrients soon.`,
          icon: '⚠️',
          action: 'Get Recommendations'
        });
      }

      // Harvest alert
      const daysLeft = this.farmerDataService.daysToHarvest();
      if (daysLeft <= 7 && daysLeft > 0) {
        alerts.push({
          type: 'info',
          title: 'Harvest Time Approaching',
          message: `Your ${farm.current_crop} is ready to harvest in ${daysLeft} days.`,
          icon: '🌾',
          action: 'Prepare Harvest'
        });
      }
    }

    if (analytics?.recommendations) {
      const urgentRecs = analytics.recommendations.filter(r => r.includes('URGENT'));
      if (urgentRecs.length > 0) {
        alerts.push({
          type: 'danger',
          title: 'Urgent Action Required',
          message: urgentRecs[0],
          icon: '🚨',
          action: 'View Recommendations'
        });
      }
    }

    // Credit score alert
    const credit = this.creditScore();
    if (credit && credit.score < 500) {
      alerts.push({
        type: 'danger',
        title: 'Low Credit Score',
        message: `Your credit score is ${credit.score}. Improve to unlock loans.`,
        icon: '💳',
        action: 'View Score'
      });
    }

    this.alertsNotifications.set(alerts);
  }

  /**
   * Setup auto-refresh every 5 minutes
   */
  private setupAutoRefresh(): void {
    const interval = setInterval(() => {
      const farmiqId = sessionStorage.getItem('farmiq_id');
      if (farmiqId && !this.loading()) {
        this.farmerDataService.refreshData();
      }
    }, 5 * 60 * 1000); // 5 minutes

    this.destroy$.subscribe(() => clearInterval(interval));
  }

  /**
   * Get color based on health percentage
   */
  private getHealthColor(value: number): string {
    if (value > 70) return 'success';
    if (value > 50) return 'warning';
    return 'danger';
  }

  /**
   * Get credit rating label
   */
  private getCreditRating(score: number): string {
    if (score >= 750) return 'Excellent';
    if (score >= 700) return 'Very Good';
    if (score >= 650) return 'Good';
    if (score >= 600) return 'Fair';
    return 'Poor';
  }

  /**
   * Get color based on credit score
   */
  private getCreditColor(score: number): string {
    if (score >= 750) return 'success';
    if (score >= 650) return 'primary';
    if (score >= 600) return 'warning';
    return 'danger';
  }

  /**
   * Navigate to detail page
   */
  goTo(path: string): void {
    // Implement navigation
    console.log('Navigate to:', path);
  }

  /**
   * Refresh the dashboard data manually
   */
  refreshDashboard(): void {
    this.refreshing.set(true);
    this.farmerDataService.refreshData();
    
    const farmiqId = sessionStorage.getItem('farmiq_id');
    if (farmiqId) {
      this.farmerCreditService.getCreditScore(farmiqId).pipe(takeUntil(this.destroy$)).subscribe(() => {
        this.refreshing.set(false);
      });
    } else {
      this.refreshing.set(false);
    }
  }
}
