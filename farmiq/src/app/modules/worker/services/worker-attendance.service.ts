/**
 * Worker Attendance Service
 * Handles attendance tracking, punch in/out, and attendance reporting
 */

import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';

export interface AttendanceRecord {
  id: string;
  workerId: string;
  punchInTime: string;
  punchOutTime?: string;
  duration?: number; // in minutes
  status: 'present' | 'late' | 'absent' | 'half_day' | 'excused';
  location?: string;
  notes?: string;
  verifiedBy?: string;
  date: string;
}

export interface AttendanceSummary {
  workerId: string;
  totalDays: number;
  presentDays: number;
  absentDays: number;
  lateDays: number;
  excusedDays: number;
  attendanceRate: number; // percentage
  avgDailyHours: number;
  trend: 'improving' | 'stable' | 'declining';
}

export interface AttendanceLeaveRequest {
  id: string;
  workerId: string;
  leaveType: 'sick' | 'personal' | 'maternity' | 'compassionate' | 'unpaid';
  startDate: string;
  endDate: string;
  reason: string;
  status: 'pending' | 'approved' | 'rejected';
  approvedBy?: string;
  approvalDate?: string;
  daysRequested: number;
}

@Injectable({ providedIn: 'root' })
export class WorkerAttendanceService {
  private apiUrl = environment.apiUrl;
  private supabaseUrl = `${environment.supabase.url}/rest/v1`;

  // ========== STATE ==========
  todayAttendance = signal<AttendanceRecord[]>([]);
  monthAttendance = signal<AttendanceRecord[]>([]);
  workerSummary = signal<AttendanceSummary | null>(null);
  leaveRequests = signal<AttendanceLeaveRequest[]>([]);
  loading = signal<boolean>(false);
  error = signal<string | null>(null);
  selectedDate = signal<string>(new Date().toISOString().split('T')[0]);

  // ========== COMPUTED ==========
  punchedInWorkers = computed(() => {
    const today = this.todayAttendance();
    return today.filter(a => a.punchInTime && !a.punchOutTime);
  });

  attendanceRate = computed(() => {
    const summary = this.workerSummary();
    return summary?.attendanceRate || 0;
  });

  pendingLeaveRequests = computed(() => {
    return this.leaveRequests().filter(l => l.status === 'pending');
  });

  constructor(private http: HttpClient) {}

  /**
   * LOGIC: Punch in a worker
   * Prevents double punch-in on same day
   * Must punch out before punching in again
   */
  punchIn(workerId: string, location?: string): Observable<AttendanceRecord> {
    const today = new Date().toISOString().split('T')[0];
    
    // Check if already punched in today
    return this.checkTodayPunchStatus(workerId).pipe(
      tap((existingRecord) => {
        if (existingRecord && !existingRecord.punchOutTime) {
          throw new Error('Worker already punched in. Must punch out first.');
        }
      }),
      switchMap(() => {
        const payload = {
          worker_id: workerId,
          punch_in_time: new Date().toISOString(),
          location,
          status: this.calculateStatus(new Date()),
          date: today,
          notes: `Punched in at ${new Date().toLocaleTimeString()}`
        };

        return this.http.post<AttendanceRecord>(
          `${this.supabaseUrl}/attendance`,
          payload,
          { headers: this.getHeaders() }
        );
      }),
      tap((record: AttendanceRecord) => {
        const today_records = this.todayAttendance();
        this.todayAttendance.set([...today_records, record]);
      }),
      catchError((err) => this.handleError('Failed to punch in', err))
    );
  }

  /**
   * LOGIC: Punch out a worker
   * Calculates duration between punch in and punch out
   * Marks as half day if less than 4 hours
   */
  punchOut(workerId: string, location?: string): Observable<AttendanceRecord> {
    return this.getTodayRecord(workerId).pipe(
      switchMap((record) => {
        if (!record) {
          throw new Error('No punch in record found today.');
        }

        const punchInTime = new Date(record.punchInTime);
        const punchOutTime = new Date();
        const durationMinutes = Math.round((punchOutTime.getTime() - punchInTime.getTime()) / 60000);

        // Update record with punch out
        const updatePayload = {
          punch_out_time: punchOutTime.toISOString(),
          duration: durationMinutes,
          status: this.calculateStatus(punchOutTime, durationMinutes),
          notes: `Worked ${this.formatDuration(durationMinutes)}`
        };

        return this.http.patch<AttendanceRecord>(
          `${this.supabaseUrl}/attendance?id=eq.${record.id}`,
          updatePayload,
          { headers: this.getHeaders() }
        );
      }),
      tap((updatedRecord: AttendanceRecord) => {
        const today_records = this.todayAttendance().map(r => r.id === updatedRecord.id ? updatedRecord : r);
        this.todayAttendance.set(today_records);
      }),
      catchError((err) => this.handleError('Failed to punch out', err))
    );
  }

  /**
   * LOGIC: Calculate attendance status
   * Checks if punch in is within standard hours (before 9 AM = on time, after 9 AM = late)
   * Checks if duration < 4 hours = half day
   */
  private calculateStatus(date: Date, duration?: number): AttendanceRecord['status'] {
    const hour = date.getHours();
    let status: AttendanceRecord['status'] = 'present';

    // If punched in after 9 AM, mark as late
    if (hour >= 9) {
      status = 'late';
    }

    // If duration less than 4 hours (240 minutes), mark as half day
    if (duration && duration < 240) {
      status = 'half_day';
    }

    return status;
  }

  /**
   * Get today's punch record for a worker
   */
  private getTodayRecord(workerId: string): Observable<AttendanceRecord | null> {
    const today = new Date().toISOString().split('T')[0];
    return this.http.get<AttendanceRecord[]>(
      `${this.supabaseUrl}/attendance?worker_id=eq.${workerId}&date=eq.${today}`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((records: AttendanceRecord[]) => {
        // Return the first record
      }),
      map((records) => records.length > 0 ? records[0] : null),
      catchError((err) => throwError(() => err))
    );
  }

  /**
   * Check punch status for today
   */
  private checkTodayPunchStatus(workerId: string): Observable<AttendanceRecord | null> {
    return this.getTodayRecord(workerId);
  }

  /**
   * Get attendance for a specific date range
   */
  getAttendanceRange(workerId: string, startDate: string, endDate: string): Observable<AttendanceRecord[]> {
    this.loading.set(true);
    return this.http.get<AttendanceRecord[]>(
      `${this.supabaseUrl}/attendance?worker_id=eq.${workerId}&date=gte.${startDate}&date=lte.${endDate}&order=date.desc`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((records: AttendanceRecord[]) => {
        this.monthAttendance.set(records);
        this.loading.set(false);
      }),
      catchError((err) => this.handleError('Failed to fetch attendance', err))
    );
  }

  /**
   * Get attendance summary for a worker
   */
  getAttendanceSummary(workerId: string, period: 'monthly' | 'quarterly' | 'yearly' = 'monthly'): Observable<AttendanceSummary> {
    return this.http.get<AttendanceSummary>(
      `${this.apiUrl}/workers/${workerId}/attendance-summary?period=${period}`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((summary: AttendanceSummary) => {
        this.workerSummary.set(summary);
      }),
      catchError((err) => this.handleError('Failed to fetch summary', err))
    );
  }

  /**
   * LOGIC: Request leave
   * Validates dates and leave balance
   */
  requestLeave(workerId: string, request: Partial<AttendanceLeaveRequest>): Observable<AttendanceLeaveRequest> {
    const startDate = new Date(request.startDate!);
    const endDate = new Date(request.endDate!);
    const daysRequested = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)) + 1;

    // Validate: end date must be after start date
    if (endDate < startDate) {
      return throwError(() => new Error('End date must be after start date'));
    }

    // Validate: cannot request leave retroactively (past dates)
    if (startDate < new Date()) {
      return throwError(() => new Error('Cannot request leave for past dates'));
    }

    const payload = {
      worker_id: workerId,
      leave_type: request.leaveType,
      start_date: request.startDate,
      end_date: request.endDate,
      reason: request.reason,
      status: 'pending',
      days_requested: daysRequested
    };

    return this.http.post<AttendanceLeaveRequest>(
      `${this.supabaseUrl}/leave_requests`,
      payload,
      { headers: this.getHeaders() }
    ).pipe(
      tap((newRequest: AttendanceLeaveRequest) => {
        const updated = [...this.leaveRequests(), newRequest];
        this.leaveRequests.set(updated);
      }),
      catchError((err) => this.handleError('Failed to request leave', err))
    );
  }

  /**
   * Approve leave request (supervisor only)
   */
  approveLeaveRequest(requestId: string, approvedBy: string): Observable<AttendanceLeaveRequest> {
    return this.http.patch<AttendanceLeaveRequest>(
      `${this.supabaseUrl}/leave_requests?id=eq.${requestId}`,
      {
        status: 'approved',
        approved_by: approvedBy,
        approval_date: new Date().toISOString()
      },
      { headers: this.getHeaders() }
    ).pipe(
      tap((updated: AttendanceLeaveRequest) => {
        const requests = this.leaveRequests().map(r => r.id === requestId ? updated : r);
        this.leaveRequests.set(requests);
      }),
      catchError((err) => this.handleError('Failed to approve leave', err))
    );
  }

  /**
   * Reject leave request
   */
  rejectLeaveRequest(requestId: string): Observable<AttendanceLeaveRequest> {
    return this.http.patch<AttendanceLeaveRequest>(
      `${this.supabaseUrl}/leave_requests?id=eq.${requestId}`,
      { status: 'rejected' },
      { headers: this.getHeaders() }
    ).pipe(
      catchError((err) => this.handleError('Failed to reject leave', err))
    );
  }

  /**
   * Format duration in minutes to human readable string
   */
  private formatDuration(minutes: number): string {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  }

  /**
   * Get HTTP headers
   */
  private getHeaders() {
    const token = sessionStorage.getItem('auth_token');
    return {
      'Authorization': `Bearer ${token || ''}`,
      'apikey': environment.supabase.anonKey,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Handle errors
   */
  private handleError(message: string, error: any) {
    console.error(message, error);
    this.error.set(message);
    this.loading.set(false);
    return throwError(() => error);
  }
}

// Add missing import
import { switchMap, map } from 'rxjs/operators';
