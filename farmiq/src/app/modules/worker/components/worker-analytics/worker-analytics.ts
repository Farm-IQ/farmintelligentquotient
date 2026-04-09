/**
 * Worker Analytics Component - Comprehensive Worker Dashboard
 * Displays tasks, performance metrics, and attendance tracking
 */

import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { Subject, takeUntil, finalize } from 'rxjs';

// Models and Services
interface WorkerTask {
  id: string;
  worker_id: string;
  farm_id: string;
  task_name: string;
  task_type: 'planting' | 'weeding' | 'harvesting' | 'irrigation' | 'maintenance' | 'other';
  status: 'pending' | 'in-progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high';
  assigned_date: string;
  due_date: string;
  completion_date?: string;
  estimated_hours?: number;
  actual_hours?: number;
  quality_rating?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface WorkerPerformance {
  id: string;
  worker_id: string;
  period_start: string;
  period_end: string;
  tasks_completed: number;
  quality_rating: number;
  reliability_score: number;
  skill_rating: number;
  attendance_rate: number;
  performance_notes?: string;
  created_at: string;
  updated_at: string;
}

interface WorkerAttendance {
  id: string;
  worker_id: string;
  farm_id: string;
  date: string;
  status: 'present' | 'absent' | 'leave' | 'half_day' | 'sick_leave';
  check_in_time?: string;
  check_out_time?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

@Component({
  selector: 'app-worker-analytics',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule, IonicModule],
  templateUrl: './worker-analytics.html',
  styleUrls: ['./worker-analytics.scss']
})
export class WorkerAnalyticsComponent implements OnInit, OnDestroy {
  // State
  loading = true;
  error: string | null = null;
  errorDetails: string = '';
  activeTab = 'tasks';
  showRecordAttendanceModal = false;

  // Section Loading States
  loadingTasks = false;
  loadingPerformance = false;
  loadingAttendance = false;

  // Section Error States
  tasksError: string | null = null;
  performanceError: string | null = null;
  attendanceError: string | null = null;

  // Data
  assignedTasks: WorkerTask[] = [];
  parentOpenTasks: WorkerTask[] = [];
  completedTasks: WorkerTask[] = [];
  performanceMetrics: WorkerPerformance | null = null;
  attendanceHistory: WorkerAttendance[] = [];
  currentUser: any = null;

  // Forms
  attendanceForm!: FormGroup;

  // Statistics
  taskStats = {
    pending: 0,
    inProgress: 0,
    completed: 0,
    completionRate: 0
  };

  performanceStats = {
    avgQualityRating: 0,
    avgReliabilityScore: 0,
    avgSkillRating: 0,
    attendanceRate: 0
  };

  private destroy$ = new Subject<void>();

  constructor(
    private formBuilder: FormBuilder
  ) {
    this.initializeForms();
  }

  ngOnInit(): void {
    console.log('🚜 Loading Worker Dashboard...');
    this.loadWorkerData();
    // Refresh every 5 minutes
    setInterval(() => this.refreshWorkerData(), 5 * 60 * 1000);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ========================================================================
  // INITIALIZATION & FORMS
  // ========================================================================

  private initializeForms(): void {
    this.attendanceForm = this.formBuilder.group({
      attendance_date: [new Date().toISOString().split('T')[0], Validators.required],
      status: ['present', Validators.required],
      check_in_time: [''],
      check_out_time: [''],
      notes: ['']
    });
  }

  // ========================================================================
  // DATA LOADING
  // ========================================================================

  private loadWorkerData(): void {
    this.loading = true;
    this.error = null;
    this.errorDetails = '';

    try {
      // Load all sections with error handling
      this._loadTasks();
      this._loadPerformanceMetrics();
      this._loadAttendance();
      this.calculateStats();
      
      this.loading = false;
      console.log('✅ Worker data loaded successfully');
    } catch (err: any) {
      this.error = 'Failed to load worker dashboard';
      this.errorDetails = this._getErrorMessage(err);
      this.loading = false;
      console.error('❌ Worker data load error:', err);
    }
  }

  private _loadTasks(): void {
    try {
      this.loadingTasks = true;
      this.tasksError = null;

      // Simulated task data - Replace with actual Supabase call when service available
      this.assignedTasks = [
        {
          id: '1',
          worker_id: 'worker1',
          farm_id: 'farm1',
          task_name: 'Weed Coffee Plot A',
          task_type: 'weeding',
          status: 'in-progress',
          priority: 'high',
          assigned_date: new Date().toISOString().split('T')[0],
          due_date: new Date(Date.now() + 2*24*60*60*1000).toISOString().split('T')[0],
          estimated_hours: 4,
          notes: 'Remove all weeds from plot A',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: '2',
          worker_id: 'worker1',
          farm_id: 'farm1',
          task_name: 'Plant Maize Seeds',
          task_type: 'planting',
          status: 'pending',
          priority: 'medium',
          assigned_date: new Date().toISOString().split('T')[0],
          due_date: new Date(Date.now() + 3*24*60*60*1000).toISOString().split('T')[0],
          estimated_hours: 6,
          notes: 'Plant maize seeds in Field 2',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ];

      this.loadingTasks = false;
      console.log(`✅ Loaded ${this.assignedTasks.length} assigned tasks`);
    } catch (err: any) {
      this.loadingTasks = false;
      this.tasksError = 'Unable to load tasks: ' + this._getErrorMessage(err);
      console.error('❌ Failed to load tasks:', err);
    }
  }

  private _loadPerformanceMetrics(): void {
    try {
      this.loadingPerformance = true;
      this.performanceError = null;

      // Simulated performance data - Replace with actual Supabase call when service available
      this.performanceMetrics = {
        id: 'perf1',
        worker_id: 'worker1',
        period_start: new Date(Date.now() - 30*24*60*60*1000).toISOString().split('T')[0],
        period_end: new Date().toISOString().split('T')[0],
        tasks_completed: 12,
        quality_rating: 4.3,
        reliability_score: 4.5,
        skill_rating: 4.2,
        attendance_rate: 92,
        performance_notes: 'Consistent performer with good attendance',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      this.loadingPerformance = false;
      console.log('✅ Loaded performance metrics');
    } catch (err: any) {
      this.loadingPerformance = false;
      this.performanceError = 'Unable to load performance data: ' + this._getErrorMessage(err);
      console.error('❌ Failed to load performance:', err);
    }
  }

  private _loadAttendance(): void {
    try {
      this.loadingAttendance = true;
      this.attendanceError = null;

      // Simulated attendance data - Replace with actual Supabase call when service available
      this.attendanceHistory = [
        {
          id: '1',
          worker_id: 'worker1',
          farm_id: 'farm1',
          date: new Date().toISOString().split('T')[0],
          status: 'present',
          check_in_time: '07:00',
          check_out_time: '17:00',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: '2',
          worker_id: 'worker1',
          farm_id: 'farm1',
          date: new Date(Date.now() - 24*60*60*1000).toISOString().split('T')[0],
          status: 'present',
          check_in_time: '07:15',
          check_out_time: '17:30',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ];

      this.loadingAttendance = false;
      console.log(`✅ Loaded ${this.attendanceHistory.length} attendance records`);
    } catch (err: any) {
      this.loadingAttendance = false;
      this.attendanceError = 'Unable to load attendance: ' + this._getErrorMessage(err);
      console.error('❌ Failed to load attendance:', err);
    }
  }

  private refreshWorkerData(): void {
    try {
      this._loadTasks();
      this._loadPerformanceMetrics();
      this._loadAttendance();
      this.calculateStats();
      console.log('✅ Worker data refreshed');
    } catch (err: any) {
      console.error('❌ Failed to refresh worker data:', err);
    }
  }

  // ========================================================================
  // TASK MANAGEMENT
  // ========================================================================

  updateTaskStatus(task: WorkerTask, newStatus: string): void {
    // Simulate status update
    const updatedIndex = this.assignedTasks.findIndex(t => t.id === task.id);
    if (updatedIndex !== -1) {
      const updatedTask = { ...this.assignedTasks[updatedIndex], status: newStatus as any };
      this.assignedTasks[updatedIndex] = updatedTask;

      if (newStatus === 'completed') {
        updatedTask.completion_date = new Date().toISOString().split('T')[0];
        this.completedTasks.push(updatedTask);
        this.assignedTasks.splice(updatedIndex, 1);
      }

      console.log('✅ Task status updated:', task.task_name);
      this.calculateStats();
    }
  }

  recordTaskHours(task: WorkerTask): void {
    console.log('Recording hours for task:', task.task_name);
    // This would open a modal for recording actual hours and quality rating
  }

  completeTask(task: WorkerTask): void {
    if (confirm(`Complete task: "${task.task_name}"?`)) {
      this.updateTaskStatus(task, 'completed');
    }
  }

  getAllPendingTasks(): WorkerTask[] {
    return this.assignedTasks.filter(t => t.status === 'pending');
  }

  getInProgressTasks(): WorkerTask[] {
    return this.assignedTasks.filter(t => t.status === 'in-progress');
  }

  // ========================================================================
  // ATTENDANCE MANAGEMENT
  // ========================================================================

  recordAttendance(): void {
    if (this.attendanceForm.invalid) {
      console.warn('Invalid attendance form');
      return;
    }

    const formData = this.attendanceForm.value;
    const attendance: WorkerAttendance = {
      id: 'att_' + Date.now(),
      worker_id: 'worker1',
      farm_id: 'farm1',
      ...formData,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    this.attendanceHistory.unshift(attendance);
    this.showRecordAttendanceModal = false;
    this.attendanceForm.reset({
      attendance_date: new Date().toISOString().split('T')[0],
      status: 'present'
    });
    console.log('✅ Attendance recorded');
  }

  // ========================================================================
  // STATISTICS CALCULATIONS
  // ========================================================================

  private calculateStats(): void {
    // Task statistics
    this.taskStats = {
      pending: this.assignedTasks.filter(t => t.status === 'pending').length,
      inProgress: this.assignedTasks.filter(t => t.status === 'in-progress').length,
      completed: this.completedTasks.length,
      completionRate: this.completedTasks.length > 0 
        ? (this.completedTasks.length / (this.assignedTasks.length + this.completedTasks.length)) * 100
        : 0
    };

    // Performance statistics
    if (this.performanceMetrics) {
      this.performanceStats = {
        avgQualityRating: this.performanceMetrics.quality_rating,
        avgReliabilityScore: this.performanceMetrics.reliability_score,
        avgSkillRating: this.performanceMetrics.skill_rating,
        attendanceRate: this.performanceMetrics.attendance_rate
      };
    }
  }

  getAttendanceRate(): number {
    if (this.attendanceHistory.length === 0) return 0;
    const presentDays = this.attendanceHistory.filter(
      a => a.status === 'present' || a.status === 'half_day'
    ).length;
    return (presentDays / this.attendanceHistory.length) * 100;
  }

  getRecentAttendance(days: number = 7): WorkerAttendance[] {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);
    return this.attendanceHistory.filter(a => new Date(a.date) >= cutoffDate);
  }

  // ========================================================================
  // UI UTILITIES
  // ========================================================================

  setActiveTab(tab: string): void {
    this.activeTab = tab;
  }

  getTaskStatusColor(status: string): string {
    switch (status) {
      case 'pending': return 'warning';
      case 'in-progress': return 'info';
      case 'completed': return 'success';
      case 'cancelled': return 'danger';
      default: return 'primary';
    }
  }

  getTaskPriorityColor(priority: string): string {
    switch (priority) {
      case 'low': return 'success';
      case 'medium': return 'warning';
      case 'high': return 'danger';
      default: return 'primary';
    }
  }

  getAttendanceStatusColor(status: string): string {
    switch (status) {
      case 'present': return 'success';
      case 'absent': return 'danger';
      case 'leave': return 'warning';
      case 'half_day': return 'info';
      default: return 'secondary';
    }
  }

  formatTaskType(type: string): string {
    return type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  }

  formatStatus(status: string): string {
    return status.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  }

  getRatingStars(rating: number): number[] {
    return Array(Math.round(rating)).fill(0);
  }

  // ========================================================================
  // ERROR HANDLING & UTILITY METHODS
  // ========================================================================

  private _getErrorMessage(error: any): string {
    if (!error) return 'An unknown error occurred';

    // Handle HTTP errors
    if (error.status) {
      switch (error.status) {
        case 0: return 'Network error. Check your internet connection.';
        case 400: return 'Invalid request. Please check your input.';
        case 401: return 'Unauthorized. Please log in again.';
        case 403: return 'You do not have permission to access this data.';
        case 404: return 'Data not found.';
        case 500: return 'Server error. Please try again later.';
        case 503: return 'Service temporarily unavailable. Please try again later.';
        default: return `Error ${error.status}: ${error.statusText || 'Unknown error'}`;
      }
    }

    // Handle Supabase errors
    if (error.message) {
      if (error.message.includes('PKEY')) return 'Duplicate entry. This record already exists.';
      if (error.message.includes('FOREIGN KEY')) return 'Invalid reference. Related record not found.';
      if (error.message.includes('NOT NULL')) return 'Required field is missing.';
      return error.message;
    }

    return 'An unexpected error occurred. Please try again.';
  }

  clearError(): void {
    this.error = null;
    this.errorDetails = '';
  }

  retryLoadAllData(): void {
    this.loadWorkerData();
  }
}
