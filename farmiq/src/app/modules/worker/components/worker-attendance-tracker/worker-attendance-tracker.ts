/**
 * Worker Attendance Tracker Component
 * Track daily worker attendance and manage timesheets
 */

import { Component, Input, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { WorkerManagementService } from '../../../farmer/services/worker-management.service';
import { FarmWorker, WorkerAttendance } from '../../models/worker-profile.models';

@Component({
  selector: 'app-worker-attendance-tracker',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="attendance-tracker">
      <!-- Add Attendance Form -->
      <div class="form-section">
        <h3>Record Attendance</h3>
        <form [formGroup]="attendanceForm" (ngSubmit)="recordAttendance()" class="attendance-form">
          <div class="form-grid">
            <div class="form-group">
              <label>Date</label>
              <input type="date" formControlName="attendance_date" />
            </div>
            <div class="form-group">
              <label>Status</label>
              <select formControlName="status">
                <option value="present">Present</option>
                <option value="absent">Absent</option>
                <option value="leave">On Leave</option>
                <option value="half_day">Half Day</option>
                <option value="sick_leave">Sick Leave</option>
              </select>
            </div>
            <div class="form-group">
              <label>Check-in Time</label>
              <input type="time" formControlName="check_in_time" />
            </div>
            <div class="form-group">
              <label>Check-out Time</label>
              <input type="time" formControlName="check_out_time" />
            </div>
          </div>
          <div class="form-group">
            <label>Notes</label>
            <textarea formControlName="notes" rows="2"></textarea>
          </div>
          <button type="submit" [disabled]="!attendanceForm.valid || isLoading" class="btn-primary">
            {{ isLoading ? 'Recording...' : 'Record Attendance' }}
          </button>
          <div *ngIf="error" class="error-message">{{ error }}</div>
          <div *ngIf="success" class="success-message">Attendance recorded successfully</div>
        </form>
      </div>

      <!-- Attendance Statistics -->
      <div class="stats-section">
        <h3>Attendance Overview</h3>
        <div class="stats-grid">
          <div class="stat-box">
            <div class="stat-label">Present Days</div>
            <div class="stat-value">{{ stats.presentDays }}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Absent Days</div>
            <div class="stat-value">{{ stats.absentDays }}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">On Leave</div>
            <div class="stat-value">{{ stats.leaveDays }}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Attendance Rate</div>
            <div class="stat-value">{{ stats.attendanceRate }}%</div>
          </div>
        </div>
      </div>

      <!-- Attendance History -->
      <div class="history-section">
        <h3>Recent Attendance</h3>
        <div class="history-list">
          <div *ngIf="attendanceHistory.length === 0" class="empty-state">
            No attendance records yet
          </div>
          <div *ngFor="let record of attendanceHistory" class="attendance-record" [ngClass]="'status-' + record.status">
            <div class="record-date">{{ record.attendance_date | date: 'MMM d, y' }}</div>
            <div class="record-status">
              <span class="status-badge">{{ formatStatus(record.status) }}</span>
            </div>
            <div class="record-time" *ngIf="record.check_in_time">
              {{ record.check_in_time }} - {{ record.check_out_time || 'N/A' }}
            </div>
            <div class="record-notes" *ngIf="record.notes">{{ record.notes }}</div>
            <div *ngIf="canApproveTimesheet" class="record-actions">
              <button (click)="approveAttendance(record)" class="btn-small btn-approve">Approve</button>
              <button (click)="rejectAttendance(record)" class="btn-small btn-reject">Reject</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Monthly Calendar View -->
      <div class="calendar-section">
        <h3>Attendance Calendar</h3>
        <div class="calendar">
          <div class="calendar-grid">
            <div *ngFor="let day of calendarDays" class="calendar-day" [ngClass]="getCalendarDayClass(day)">
              <div class="day-number">{{ day.date }}</div>
              <div class="day-status" *ngIf="day.status">{{ day.status }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .attendance-tracker {
      padding: 20px;
    }

    .form-section, .stats-section, .history-section, .calendar-section {
      background: white;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 20px;
      border: 1px solid #e0e0e0;
    }

    .form-section h3, .stats-section h3, .history-section h3, .calendar-section h3 {
      margin-top: 0;
      margin-bottom: 15px;
      color: #333;
    }

    .form-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 15px;
      margin-bottom: 15px;
    }

    .form-group {
      margin-bottom: 15px;
    }

    .form-group label {
      display: block;
      margin-bottom: 5px;
      font-weight: 500;
      color: #555;
      font-size: 13px;
    }

    .form-group input,
    .form-group select,
    .form-group textarea {
      width: 100%;
      padding: 8px 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
    }

    .form-group input:focus,
    .form-group select:focus,
    .form-group textarea:focus {
      outline: none;
      border-color: #4CAF50;
      box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
    }

    .btn-primary {
      background: #4CAF50;
      color: white;
      padding: 10px 20px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 500;
    }

    .btn-primary:hover:not(:disabled) {
      background: #45a049;
    }

    .btn-primary:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .error-message {
      color: #f44336;
      padding: 10px;
      background: #ffebee;
      border-radius: 4px;
      margin-top: 10px;
    }

    .success-message {
      color: #4CAF50;
      padding: 10px;
      background: #e8f5e9;
      border-radius: 4px;
      margin-top: 10px;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 15px;
    }

    .stat-box {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 8px;
      text-align: center;
    }

    .stat-label {
      font-size: 12px;
      text-transform: uppercase;
      opacity: 0.9;
      margin-bottom: 10px;
    }

    .stat-value {
      font-size: 28px;
      font-weight: bold;
    }

    .history-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .empty-state {
      text-align: center;
      padding: 40px;
      color: #999;
      background: #f5f5f5;
      border-radius: 4px;
    }

    .attendance-record {
      background: #f9f9f9;
      padding: 15px;
      border-radius: 6px;
      border-left: 4px solid #ddd;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 15px;
    }

    .attendance-record.status-present {
      border-left-color: #4CAF50;
    }

    .attendance-record.status-absent {
      border-left-color: #f44336;
    }

    .attendance-record.status-leave {
      border-left-color: #ff9800;
    }

    .record-date {
      font-weight: 500;
      color: #333;
      min-width: 100px;
    }

    .status-badge {
      padding: 4px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
      background: #e3f2fd;
      color: #1976d2;
    }

    .record-time {
      color: #666;
      font-size: 13px;
    }

    .record-notes {
      color: #999;
      font-size: 12px;
      flex: 1;
    }

    .record-actions {
      display: flex;
      gap: 5px;
    }

    .btn-small {
      padding: 4px 8px;
      border: none;
      border-radius: 4px;
      font-size: 12px;
      cursor: pointer;
    }

    .btn-approve {
      background: #4CAF50;
      color: white;
    }

    .btn-reject {
      background: #f44336;
      color: white;
    }

    .calendar {
      margin-top: 15px;
    }

    .calendar-grid {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 5px;
    }

    .calendar-day {
      aspect-ratio: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      border: 1px solid #e0e0e0;
      border-radius: 4px;
      background: white;
      font-size: 12px;
    }

    .calendar-day.present {
      background: #e8f5e9;
      border-color: #4CAF50;
    }

    .calendar-day.absent {
      background: #ffebee;
      border-color: #f44336;
    }

    .calendar-day.leave {
      background: #fff3e0;
      border-color: #ff9800;
    }

    .day-number {
      font-weight: 500;
    }

    .day-status {
      font-size: 10px;
      color: #666;
    }
  `]
})
export class WorkerAttendanceTrackerComponent implements OnInit {
  @Input() selectedWorker: FarmWorker | null = null;
  @Input() farmId: string = '';
  @Input() canApproveTimesheet = false;

  private fb = inject(FormBuilder);
  private workerService = inject(WorkerManagementService);

  attendanceForm!: FormGroup;
  attendanceHistory: WorkerAttendance[] = [];
  calendarDays: any[] = [];
  
  isLoading = false;
  error: string | null = null;
  success = false;

  stats = {
    presentDays: 0,
    absentDays: 0,
    leaveDays: 0,
    attendanceRate: 0,
  };

  ngOnInit(): void {
    this.initializeForm();
    this.loadAttendanceData();
    this.generateCalendarDays();
  }

  private initializeForm(): void {
    this.attendanceForm = this.fb.group({
      attendance_date: [new Date().toISOString().split('T')[0], [Validators.required]],
      status: ['present', [Validators.required]],
      check_in_time: [''],
      check_out_time: [''],
      notes: [''],
    });
  }

  private loadAttendanceData(): void {
    if (!this.selectedWorker) return;

    const today = new Date();
    const startDate = new Date(today.getFullYear(), 0, 1).toISOString().split('T')[0];
    const endDate = today.toISOString().split('T')[0];

    this.workerService.getAttendanceHistory(this.selectedWorker.id, startDate, endDate)
      .then(history => {
        this.attendanceHistory = history;
        this.calculateStats();
      })
      .catch(err => {
        this.error = 'Failed to load attendance: ' + err.message;
      });
  }

  private calculateStats(): void {
    if (!this.selectedWorker) return;
    const month = new Date().toISOString().split('T')[0].substring(0, 7);
    this.workerService.getAttendanceStats(this.selectedWorker.id, month)
      .then(stats => {
        this.stats = {
          presentDays: stats.presentDays,
          absentDays: stats.absentDays,
          leaveDays: stats.onLeaveDays,
          attendanceRate: stats.attendanceRate,
        };
      })
      .catch(err => {
        this.error = 'Failed to calculate stats: ' + err.message;
      });
  }

  private generateCalendarDays(): void {
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    
    this.calendarDays = [];
    for (let i = 0; i < firstDay.getDay(); i++) {
      this.calendarDays.push({ date: '', status: '' });
    }

    for (let date = 1; date <= lastDay.getDate(); date++) {
      const attendanceRecord = this.attendanceHistory.find(
        a => new Date(a.attendance_date || a.date || '').getDate() === date
      );
      this.calendarDays.push({
        date,
        status: attendanceRecord?.status || '',
      });
    }
  }

  recordAttendance(): void {
    if (!this.selectedWorker || !this.attendanceForm.valid) return;

    this.isLoading = true;
    this.success = false;
    this.error = null;

    const formValue = this.attendanceForm.value;
    const attendance: Omit<WorkerAttendance, 'id' | 'created_at'> = {
      worker_id: this.selectedWorker.id,
      farm_id: this.farmId,
      attendance_date: formValue.attendance_date,
      date: formValue.attendance_date,
      status: formValue.status,
      check_in_time: formValue.check_in_time,
      check_out_time: formValue.check_out_time,
      notes: formValue.notes,
    };

    this.workerService.recordAttendance(this.selectedWorker.id, this.farmId, attendance as any)
      .then(() => {
        this.success = true;
        this.attendanceForm.reset();
        this.loadAttendanceData();
        setTimeout(() => this.success = false, 3000);
        this.isLoading = false;
      })
      .catch(err => {
        this.error = err.message;
        this.isLoading = false;
      });
  }

  approveAttendance(record: WorkerAttendance): void {
    // Implementation for approving timesheet
    console.log('Approving attendance:', record);
  }

  rejectAttendance(record: WorkerAttendance): void {
    // Implementation for rejecting timesheet
    console.log('Rejecting attendance:', record);
  }

  formatStatus(status: string): string {
    return status.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  }

  getCalendarDayClass(day: any): string {
    if (!day.status) return '';
    return day.status;
  }
}
