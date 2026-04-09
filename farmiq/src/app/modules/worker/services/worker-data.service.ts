/**
 * Worker Data Service
 * Handles worker profiles, roles, permissions, and basic management
 */

import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';

export interface FarmWorker {
  id: string;
  farmiqId: string;
  farmId: string;
  firstName: string;
  lastName: string;
  email?: string;
  phone: string;
  idNumber: string;
  dateOfBirth: string;
  joinDate: string;
  status: 'active' | 'inactive' | 'suspended' | 'terminated';
  role: 'supervisor' | 'field_worker' | 'equipment_operator' | 'seasonal';
  department: string;
  baseSalary: number;
  currency: string;
  profilePhoto?: string;
  emergencyContact: {
    name: string;
    phone: string;
    relationship: string;
  };
}

export interface WorkerRole {
  name: 'supervisor' | 'field_worker' | 'equipment_operator' | 'seasonal';
  permissions: {
    canManageOtherWorkers: boolean;
    canApproveTimesheet: boolean;
    canViewPayroll: boolean;
    canViewAnalytics: boolean;
    canManageTasks: boolean;
    canManageEquipment: boolean;
    canGenerateReports: boolean;
  };
  responsibilities: string[];
  allowedOperations: string[];
}

export interface WorkerStatistics {
  totalWorkers: number;
  activeWorkers: number;
  inactiveWorkers: number;
  averageAttendance: number;
  averagePerformance: number;
  totalPayrollMonthly: number;
  highPerformers: FarmWorker[];
  lowPerformers: FarmWorker[];
}

@Injectable({ providedIn: 'root' })
export class WorkerDataService {
  private apiUrl = environment.apiUrl;
  private supabaseUrl = `${environment.supabase.url}/rest/v1`;

  // ========== STATE ==========
  workers = signal<FarmWorker[]>([]);
  selectedWorker = signal<FarmWorker | null>(null);
  statistics = signal<WorkerStatistics | null>(null);
  loading = signal<boolean>(false);
  error = signal<string | null>(null);
  filterRole = signal<string>('all');
  filterStatus = signal<string>('active');

  // ========== COMPUTED ==========
  filteredWorkers = computed(() => {
    let filtered = this.workers();
    
    if (this.filterRole() !== 'all') {
      filtered = filtered.filter(w => w.role === this.filterRole());
    }
    
    if (this.filterStatus() !== 'all') {
      filtered = filtered.filter(w => w.status === this.filterStatus());
    }
    
    return filtered;
  });

  activeWorkerCount = computed(() => 
    this.workers().filter(w => w.status === 'active').length
  );

  supervisors = computed(() => 
    this.workers().filter(w => w.role === 'supervisor' && w.status === 'active')
  );

  fieldWorkers = computed(() => 
    this.workers().filter(w => w.role === 'field_worker' && w.status === 'active')
  );

  constructor(private http: HttpClient) {}

  /**
   * Get all workers for a farm
   */
  getWorkers(farmId: string, status?: string): Observable<FarmWorker[]> {
    this.loading.set(true);
    let url = `${this.supabaseUrl}/worker_profiles?farm_id=eq.${farmId}`;
    if (status) url += `&status=eq.${status}`;

    return this.http.get<FarmWorker[]>(
      url,
      { headers: this.getHeaders() }
    ).pipe(
      tap((workersData: FarmWorker[]) => {
        this.workers.set(workersData);
        this.loading.set(false);
        this.error.set(null);
      }),
      catchError((err) => this.handleError('Failed to fetch workers', err))
    );
  }

  /**
   * Get single worker by ID
   */
  getWorker(workerId: string): Observable<FarmWorker[]> {
    return this.http.get<FarmWorker[]>(
      `${this.supabaseUrl}/worker_profiles?id=eq.${workerId}`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((workers: FarmWorker[]) => {
        if (workers.length > 0) {
          this.selectedWorker.set(workers[0]);
        }
      }),
      catchError((err) => this.handleError('Failed to fetch worker', err))
    );
  }

  /**
   * Create new worker
   */
  createWorker(farmId: string, workerData: Partial<FarmWorker>): Observable<FarmWorker> {
    const payload = {
      farm_id: farmId,
      first_name: workerData.firstName,
      last_name: workerData.lastName,
      email: workerData.email,
      phone: workerData.phone,
      id_number: workerData.idNumber,
      date_of_birth: workerData.dateOfBirth,
      join_date: new Date().toISOString(),
      status: 'active',
      role: workerData.role,
      department: workerData.department,
      base_salary: workerData.baseSalary,
      currency: workerData.currency || 'KES',
      emergency_contact: workerData.emergencyContact
    };

    return this.http.post<FarmWorker>(
      `${this.supabaseUrl}/worker_profiles`,
      payload,
      { headers: this.getHeaders() }
    ).pipe(
      tap((newWorker: FarmWorker) => {
        const updated = [...this.workers(), newWorker];
        this.workers.set(updated);
      }),
      catchError((err) => this.handleError('Failed to create worker', err))
    );
  }

  /**
   * Update worker information
   */
  updateWorker(workerId: string, updates: Partial<FarmWorker>): Observable<FarmWorker> {
    const payload: any = {};
    if (updates.firstName) payload.first_name = updates.firstName;
    if (updates.lastName) payload.last_name = updates.lastName;
    if (updates.phone) payload.phone = updates.phone;
    if (updates.email) payload.email = updates.email;
    if (updates.status) payload.status = updates.status;
    if (updates.role) payload.role = updates.role;
    if (updates.department) payload.department = updates.department;
    if (updates.baseSalary) payload.base_salary = updates.baseSalary;

    return this.http.patch<FarmWorker>(
      `${this.supabaseUrl}/worker_profiles?id=eq.${workerId}`,
      payload,
      { headers: this.getHeaders() }
    ).pipe(
      tap((updatedWorker: FarmWorker) => {
        const updated = this.workers().map(w => w.id === workerId ? updatedWorker : w);
        this.workers.set(updated);
        if (this.selectedWorker()?.id === workerId) {
          this.selectedWorker.set(updatedWorker);
        }
      }),
      catchError((err) => this.handleError('Failed to update worker', err))
    );
  }

  /**
   * Deactivate worker
   */
  deactivateWorker(workerId: string, reason: string): Observable<FarmWorker> {
    return this.updateWorker(workerId, { status: 'inactive' });
  }

  /**
   * Reactivate worker
   */
  reactivateWorker(workerId: string): Observable<FarmWorker> {
    return this.updateWorker(workerId, { status: 'active' });
  }

  /**
   * Get worker statistics
   */
  getStatistics(farmId: string): Observable<WorkerStatistics> {
    this.loading.set(true);
    return this.http.get<WorkerStatistics>(
      `${this.apiUrl}/farms/${farmId}/worker-statistics`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((stats: WorkerStatistics) => {
        this.statistics.set(stats);
        this.loading.set(false);
      }),
      catchError((err) => this.handleError('Failed to fetch statistics', err))
    );
  }

  /**
   * LOGIC: Get role permissions
   */
  getRolePermissions(role: FarmWorker['role']): WorkerRole {
    const roleConfig: Record<FarmWorker['role'], WorkerRole> = {
      supervisor: {
        name: 'supervisor',
        permissions: {
          canManageOtherWorkers: true,
          canApproveTimesheet: true,
          canViewPayroll: true,
          canViewAnalytics: true,
          canManageTasks: true,
          canManageEquipment: true,
          canGenerateReports: true
        },
        responsibilities: [
          'Oversee daily farm operations',
          'Manage team schedules',
          'Review performance',
          'Approve timesheets'
        ],
        allowedOperations: [
          'create_worker',
          'edit_worker',
          'delete_worker',
          'approve_timesheet',
          'view_payroll',
          'generate_reports'
        ]
      },
      field_worker: {
        name: 'field_worker',
        permissions: {
          canManageOtherWorkers: false,
          canApproveTimesheet: false,
          canViewPayroll: false,
          canViewAnalytics: false,
          canManageTasks: true,
          canManageEquipment: false,
          canGenerateReports: false
        },
        responsibilities: [
          'Perform fieldwork',
          'Maintain equipment',
          'Report daily activities',
          'Follow safety procedures'
        ],
        allowedOperations: [
          'view_own_timesheet',
          'view_own_performance',
          'manage_own_tasks'
        ]
      },
      equipment_operator: {
        name: 'equipment_operator',
        permissions: {
          canManageOtherWorkers: false,
          canApproveTimesheet: false,
          canViewPayroll: false,
          canViewAnalytics: false,
          canManageTasks: false,
          canManageEquipment: true,
          canGenerateReports: false
        },
        responsibilities: [
          'Operate farm equipment',
          'Conduct maintenance',
          'Report equipment issues',
          'Maintain safety logs'
        ],
        allowedOperations: [
          'view_equipment',
          'log_maintenance',
          'report_issues'
        ]
      },
      seasonal: {
        name: 'seasonal',
        permissions: {
          canManageOtherWorkers: false,
          canApproveTimesheet: false,
          canViewPayroll: false,
          canViewAnalytics: false,
          canManageTasks: false,
          canManageEquipment: false,
          canGenerateReports: false
        },
        responsibilities: [
          'Perform assigned tasks',
          'Follow instructions',
          'Maintain work area',
          'Report daily status'
        ],
        allowedOperations: [
          'view_own_timesheet'
        ]
      }
    };

    return roleConfig[role];
  }

  /**
   * LOGIC: Check if user has permission
   */
  hasPermission(role: FarmWorker['role'], permission: keyof WorkerRole['permissions']): boolean {
    const rolePerms = this.getRolePermissions(role);
    return rolePerms.permissions[permission] || false;
  }

  /**
   * LOGIC: Get allowed operations for a role
   */
  getAllowedOperations(role: FarmWorker['role']): string[] {
    return this.getRolePermissions(role).allowedOperations;
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
