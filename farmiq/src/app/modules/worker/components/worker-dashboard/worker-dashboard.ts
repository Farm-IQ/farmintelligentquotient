/**
 * Worker Dashboard Component - Modern UI
 * Role-based dashboard with quick stats, tasks, attendance, and performance
 */

import { Component, OnInit, OnDestroy, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { WorkerDataService, FarmWorker } from '../../services/worker-data.service';
import { WorkerAttendanceService } from '../../services/worker-attendance.service';
import { WorkerPayrollService } from '../../services/worker-payroll.service';
import { WorkerTaskService } from '../../services/worker-task.service';
import { WorkerPerformanceService } from '../../services/worker-performance.service';


interface DashboardMetric {
  label: string;
  value: string | number;
  icon: string;
  color: string;
  trend?: 'up' | 'down' | 'stable';
  comparison?: string;
}

interface DashboardAlert {
  type: 'info' | 'warning' | 'danger' | 'success';
  icon: string;
  title: string;
  message: string;
  action?: string;
}

@Component({
  selector: 'app-worker-dashboard',
  standalone: true,
  imports: [CommonModule, IonicModule],
  templateUrl: './worker-dashboard.html',
  styleUrls: ['./worker-dashboard.scss']
})
export class WorkerDashboardComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  private farmId = sessionStorage.getItem('farm_id') || '';
  private workerId = sessionStorage.getItem('worker_id') || '';

  // ========== DATA FROM SERVICES ==========
  workers = computed(() => this.workerDataService.workers());
  activeWorkers = computed(() => this.workerDataService.activeWorkerCount());
  loading = computed(() => this.workerDataService.loading());
  error = computed(() => this.workerDataService.error());

  // Attendance data
  punchedInWorkers = computed(() => this.attendanceService.punchedInWorkers());
  attendanceRate = computed(() => this.attendanceService.attendanceRate());

  // Payroll data
  totalPayroll = computed(() => this.payrollService.totalNetPayroll());
  totalTax = computed(() => this.payrollService.totalTaxDeduction());

  // Task data
  activeTasks = computed(() => this.taskService.activeTasks());
  overdueTasks = computed(() => this.taskService.overdueTasks());

  // Performance data
  avgPerformanceScore = computed(() => this.performanceService.averageScore());
  performanceTrend = computed(() => this.performanceService.performanceTrend());

  // ========== UI STATE ==========
  metrics = signal<DashboardMetric[]>([]);
  alerts = signal<DashboardAlert[]>([]);
  selectedTab = signal<'overview' | 'workers' | 'tasks' | 'attendance'>('overview');
  refreshing = signal<boolean>(false);
  userRole = signal<FarmWorker['role']>('field_worker');

  // ========== PERMISSIONS ==========
  canManageWorkers = computed(() => {
    const role = this.userRole();
    return this.workerDataService.hasPermission(role, 'canManageOtherWorkers');
  });

  canViewPayroll = computed(() => {
    const role = this.userRole();
    return this.workerDataService.hasPermission(role, 'canViewPayroll');
  });

  canViewAnalytics = computed(() => {
    const role = this.userRole();
    return this.workerDataService.hasPermission(role, 'canViewAnalytics');
  });

  // ========== COMPUTED FILTERED DATA FOR TEMPLATES ==========
  // Attendance status counts for supervisor (from attendance service)
  presentWorkers = computed(() => 0);
  lateWorkers = computed(() => 0);
  absentWorkers = computed(() => 0);
  onLeaveWorkers = computed(() => 0);

  // Performance distribution (based on average performance score)
  excellentPerformance = computed(() => 0);
  goodPerformance = computed(() => 0);
  averagePerformance = computed(() => 0);
  poorPerformance = computed(() => 0);

  // Task counts
  overdueTasksCount = computed(() => (this.activeTasks() || []).filter(t => t.status === 'overdue').length);
  completedTodayCount = computed(() => (this.activeTasks() || []).filter(t => t.status === 'completed').length);

  // Local UI state
  currentTime = signal<Date>(new Date());
  isPunchedIn = signal<boolean>(false);
  todayHours = signal<number>(0);
  selectedWorker = signal<FarmWorker | null>(null);
  myActiveTasks = computed(() => (this.activeTasks() || []).slice(0, 5));
  myPerformanceScore = signal<number>(0);
  lastPunchTime = signal<Date | null>(null);
  mapProviderInfo = signal<{ provider: string; isTomTomEnabled: boolean; apiConfigured: boolean } | null>(null);

  constructor(
    private workerDataService: WorkerDataService,
    private attendanceService: WorkerAttendanceService,
    private payrollService: WorkerPayrollService,
    private taskService: WorkerTaskService,
    private performanceService: WorkerPerformanceService
  ) {}

  ngOnInit(): void {
    this.loadDashboardData();
    this.setupAutoRefresh();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load all dashboard data based on user role
   */
  private loadDashboardData(): void {
    const role = this.userRole();

    // Get workers if supervisor or admin
    if (this.workerDataService.hasPermission(role, 'canManageOtherWorkers')) {
      this.workerDataService.getWorkers(this.farmId, 'active')
        .pipe(takeUntil(this.destroy$))
        .subscribe();

      this.workerDataService.getStatistics(this.farmId)
        .pipe(takeUntil(this.destroy$))
        .subscribe();

      this.attendanceService.getAttendanceRange(
        this.farmId,
        new Date().toISOString().split('T')[0],
        new Date().toISOString().split('T')[0]
      ).pipe(takeUntil(this.destroy$)).subscribe();
    }

    // Get own data
    this.attendanceService.getAttendanceSummary(this.workerId)
      .pipe(takeUntil(this.destroy$))
      .subscribe();

    this.payrollService.getWorkerPayroll(this.workerId, 3)
      .pipe(takeUntil(this.destroy$))
      .subscribe();

    this.taskService.getWorkerTasks(this.workerId)
      .pipe(takeUntil(this.destroy$))
      .subscribe();

    this.performanceService.getWorkerEvaluations(this.workerId)
      .pipe(takeUntil(this.destroy$))
      .subscribe();

    this.updateMetrics();
    this.generateAlerts();
  }

  /**
   * LOGIC: Calculate and display key metrics
   */
  private updateMetrics(): void {
    const metricsArray: DashboardMetric[] = [];

    // Attendance metric
    const attendance = this.attendanceRate() || 0;
    metricsArray.push({
      label: 'Attendance Rate',
      value: `${Math.round(attendance)}%`,
      icon: '📋',
      color: attendance > 90 ? 'success' : attendance > 70 ? 'warning' : 'danger',
      trend: attendance > 85 ? 'up' : 'stable'
    });

    // Active workers (supervisor view)
    if (this.canManageWorkers()) {
      metricsArray.push({
        label: 'Active Workers',
        value: this.activeWorkers(),
        icon: '👥',
        color: 'primary',
        comparison: 'This month'
      });

      // Payroll metric
      metricsArray.push({
        label: 'Monthly Payroll',
        value: `KES ${(this.totalPayroll() / 1000).toFixed(1)}K`,
        icon: '💰',
        color: 'primary'
      });

      // Task completion
      const totalTasks = this.activeTasks().length + this.overdueTasks().length;
      const completedRate = totalTasks > 0 ? ((totalTasks - this.overdueTasks().length) / totalTasks) * 100 : 0;
      metricsArray.push({
        label: 'Task Completion',
        value: `${Math.round(completedRate)}%`,
        icon: '✓',
        color: completedRate > 70 ? 'success' : 'warning'
      });
    }

    // Performance metric
    const perfScore = this.avgPerformanceScore() || 0;
    metricsArray.push({
      label: 'Performance Score',
      value: perfScore > 0 ? perfScore.toFixed(1) : 'N/A',
      icon: '⭐',
      color: perfScore > 4 ? 'success' : perfScore > 3 ? 'primary' : 'warning',
      trend: (this.performanceTrend() as 'up' | 'down' | 'stable') || 'stable'
    });

    // Active tasks
    const activeCounts = this.activeTasks().length;
    metricsArray.push({
      label: 'Active Tasks',
      value: activeCounts,
      icon: '📌',
      color: activeCounts > 5 ? 'warning' : 'primary'
    });

    this.metrics.set(metricsArray);
  }

  /**
   * LOGIC: Generate alerts based on dashboard data
   */
  private generateAlerts(): void {
    const alertsList: DashboardAlert[] = [];

    // Attendance alert
    const attendance = this.attendanceRate();
    if (attendance < 80 && attendance > 0) {
      alertsList.push({
        type: 'warning',
        icon: '⚠️',
        title: 'Low Attendance',
        message: `Your attendance rate is ${Math.round(attendance)}%. Aim for 90%+`,
        action: 'View Details'
      });
    }

    // Overdue tasks alert
    const overdue = this.overdueTasks().length;
    if (overdue > 0) {
      alertsList.push({
        type: 'danger',
        icon: '⏰',
        title: 'Overdue Tasks',
        message: `You have ${overdue} overdue task${overdue > 1 ? 's' : ''}. Review and complete ASAP.`,
        action: 'View Tasks'
      });
    }

    // Performance alert
    const perfScore = this.avgPerformanceScore() || 0;
    if (perfScore < 3 && perfScore > 0) {
      alertsList.push({
        type: 'warning',
        icon: '📊',
        title: 'Performance Review Needed',
        message: 'Your performance score suggests areas for improvement.',
        action: 'See Feedback'
      });
    }

    // Supervisor alerts
    if (this.canManageWorkers()) {
      // Workers not punched in
      const notPunchedIn = this.workers().length - this.punchedInWorkers().length;
      if (notPunchedIn > 0) {
        alertsList.push({
          type: 'info',
          icon: 'ℹ️',
          title: 'Attendance Check',
          message: `${notPunchedIn} worker${notPunchedIn > 1 ? 's' : ''} not yet punched in today.`,
          action: 'View Attendance'
        });
      }

      // Payroll processing alert
      const currentPeriod = this.payrollService.getCurrentPeriod();
      alertsList.push({
        type: 'info',
        icon: '📅',
        title: 'Payroll Processing',
        message: `Current period: ${currentPeriod}. Review before month end.`,
        action: 'View Payroll'
      });
    }

    this.alerts.set(alertsList);
  }

  /**
   * Setup auto-refresh every 5 minutes
   */
  private setupAutoRefresh(): void {
    const interval = setInterval(() => {
      this.refreshDashboard();
    }, 5 * 60 * 1000);

    this.destroy$.subscribe(() => clearInterval(interval));
  }

  /**
   * Refresh dashboard data
   */
  refreshDashboard(): void {
    this.refreshing.set(true);
    this.loadDashboardData();
    setTimeout(() => this.refreshing.set(false), 1000);
  }

  /**
   * Punch in worker
   */
  punchIn(): void {
    this.attendanceService.punchIn(this.workerId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.updateMetrics();
          this.generateAlerts();
          console.log('Punched in successfully');
        },
        error: (err) => {
          console.error('Punch in failed:', err);
        }
      });
  }

  /**
   * Punch out worker
   */
  punchOut(): void {
    this.attendanceService.punchOut(this.workerId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.updateMetrics();
          console.log('Punched out successfully');
        },
        error: (err) => {
          console.error('Punch out failed:', err);
        }
      });
  }

  /**
   * Navigate to section
   */
  goToSection(section: string): void {
    console.log('Navigate to:', section);
  }
}
