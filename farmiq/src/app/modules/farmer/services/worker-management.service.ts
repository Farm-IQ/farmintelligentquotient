/**
 * Worker Management Service
 * 
 * Handles:
 * - Creating worker accounts for farm workers
 * - Generating temporary passwords for workers
 * - Managing worker profile information
 * - Assigning workers to farms
 * - Worker role assignment
 */

import { Injectable } from '@angular/core';
import { SupabaseService } from '../../auth/services/supabase';
import { BehaviorSubject, Observable } from 'rxjs';
import { WorkerAttendance, WorkerPayroll, WorkerPerformance, WorkerTask, FarmWorker } from '../../worker/models/worker-profile.models';

/**
 * Worker profile for internal service use during account creation
 */
export interface WorkerProfile {
  id?: string;
  user_id: string;
  farm_id: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  national_id?: string;
  position: string;
  contract_type: 'full-time' | 'part-time' | 'seasonal' | 'casual';
  hire_date: string;
  salary?: number;
  status: 'active' | 'inactive' | 'suspended';
  temporary_password?: string;
  password_shown: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface WorkerCreateRequest {
  farm_id: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  position: string;
  contract_type: 'full-time' | 'part-time' | 'seasonal' | 'casual';
  hire_date: string;
  national_id?: string;
  salary?: number;
}

/**
 * Re-export common types for convenience
 */
export type { WorkerAttendance, WorkerPayroll, WorkerPerformance, WorkerTask, FarmWorker };

@Injectable({
  providedIn: 'root'
})
export class WorkerManagementService {
  private farmWorkers$ = new BehaviorSubject<FarmWorker[]>([]);
  private currentWorker$ = new BehaviorSubject<WorkerProfile | null>(null);
  private isLoading$ = new BehaviorSubject<boolean>(false);
  private error$ = new BehaviorSubject<string | null>(null);

  constructor(private supabase: SupabaseService) {}

  /**
   * Get all workers for a farm
   */
  getFarmWorkers(farmId: string): Observable<FarmWorker[]> {
    this.loadFarmWorkers(farmId);
    return this.farmWorkers$.asObservable();
  }

  /**
   * Load farm workers from database
   */
  private async loadFarmWorkers(farmId: string): Promise<void> {
    try {
      const client = await this.supabase.getSupabaseClient();
      const { data, error } = await client
        .from('farm_workers')
        .select('*')
        .eq('farm_id', farmId)
        .eq('status', 'active')
        .order('hire_date', { ascending: false });

      if (error) throw error;

      this.farmWorkers$.next(data || []);
    } catch (error) {
      console.error('Error loading farm workers:', error);
      this.farmWorkers$.next([]);
    }
  }

  /**
   * Create a new worker account
   * Generates temporary password and creates auth user
   */
  async createWorker(request: WorkerCreateRequest): Promise<{ worker: WorkerProfile; password: string }> {
    try {
      const client = await this.supabase.getSupabaseClient();

      // Get current user (farm owner/manager)
      const { data: { user } } = await client.auth.getUser();
      if (!user) throw new Error('No authenticated user found');

      // Generate temporary password
      const tempPassword = this.generateTemporaryPassword();

      // Create auth account for worker
      const { data: authData, error: authError } = await client.auth.admin.createUser({
        email: this.generateWorkerEmail(request, request.farm_id),
        password: tempPassword,
        email_confirm: true, // Auto-confirm email
        user_metadata: {
          role: 'worker',
          farm_id: request.farm_id,
          first_name: request.first_name,
          last_name: request.last_name
        }
      });

      if (authError) throw new Error(`Failed to create auth account: ${authError.message}`);
      if (!authData.user) throw new Error('No user returned from auth creation');

      // Create worker profile record
      const { data: workerData, error: workerError } = await client
        .from('farm_workers')
        .insert({
          user_id: authData.user.id,
          farm_id: request.farm_id,
          first_name: request.first_name,
          last_name: request.last_name,
          phone_number: request.phone_number,
          national_id: request.national_id || null,
          position: request.position,
          contract_type: request.contract_type,
          hire_date: request.hire_date,
          salary: request.salary || null,
          status: 'active',
          password_shown: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        } as any)
        .select()
        .single();

      if (workerError) {
        // Cleanup: delete auth user if worker profile creation fails
        await client.auth.admin.deleteUser(authData.user.id);
        throw new Error(`Failed to create worker profile: ${workerError.message}`);
      }

      // Create worker role assignment
      const { error: roleError } = await client
        .from('user_roles')
        .insert({
          user_id: authData.user.id,
          role: 'worker',
          is_primary: true,
          assigned_by: user.id,
          assigned_at: new Date().toISOString(),
          metadata: {
            farm_id: request.farm_id,
            position: request.position
          }
        });

      if (roleError) {
        console.warn('Warning: Role assignment failed, but worker created:', roleError);
      }

      // Update user_profiles table with role
      await client
        .from('user_profiles')
        .update({
          primary_role: 'worker',
          profile_completed: true
        })
        .eq('id', authData.user.id);

      // Reload workers list
      await this.loadFarmWorkers(request.farm_id);

      return {
        worker: workerData as WorkerProfile,
        password: tempPassword
      };

    } catch (error: any) {
      throw new Error(error.message || 'Failed to create worker account');
    }
  }

  /**
   * Generate a secure temporary password
   * Format: Temp@[timestamp]-[random]
   */
  private generateTemporaryPassword(): string {
    const timestamp = Date.now().toString().slice(-4);
    const random = Math.random().toString(36).substring(2, 8).toUpperCase();
    const special = '!@#$%&'.split('')[Math.floor(Math.random() * 6)];
    return `Temp${special}${timestamp}${random}`;
  }

  /**
   * Generate a unique email for worker
   * Format: worker-[farmId]-[firstName].[lastName]@farmiq.local
   */
  private generateWorkerEmail(request: WorkerCreateRequest, farmId: string): string {
    const sanitized = `${request.first_name.toLowerCase()}.${request.last_name.toLowerCase()}`;
    const timestamp = Date.now();
    return `worker-${farmId}-${sanitized}-${timestamp}@farmiq.local`;
  }

  /**
   * Get worker by ID
   */
  async getWorker(workerId: string): Promise<WorkerProfile> {
    const client = await this.supabase.getSupabaseClient();
    const { data, error } = await client
      .from('farm_workers')
      .select('*')
      .eq('id', workerId)
      .single();

    if (error) throw new Error(error.message);
    return data as WorkerProfile;
  }

  /**
   * Update worker profile
   */
  async updateWorker(workerId: string, updates: Partial<WorkerProfile>): Promise<WorkerProfile> {
    const client = await this.supabase.getSupabaseClient();
    const { data, error } = await client
      .from('farm_workers')
      .update({
        ...updates,
        updated_at: new Date().toISOString()
      })
      .eq('id', workerId)
      .select()
      .single();

    if (error) throw new Error(error.message);

    // Reload workers list if available
    if (data.farm_id) {
      await this.loadFarmWorkers(data.farm_id);
    }

    return data as WorkerProfile;
  }

  /**
   * Mark password as shown (so it's not displayed again in UI)
   */
  async markPasswordAsShown(workerId: string): Promise<void> {
    const client = await this.supabase.getSupabaseClient();
    const { error } = await client
      .from('farm_workers')
      .update({
        password_shown: true,
        updated_at: new Date().toISOString()
      })
      .eq('id', workerId);

    if (error) throw new Error(error.message);
  }

  /**
   * Regenerate password for worker
   */
  async regeneratePassword(workerId: string): Promise<string> {
    const worker = await this.getWorker(workerId);
    const newPassword = this.generateTemporaryPassword();

    // Update auth password
    const client = await this.supabase.getSupabaseClient();
    const { error: updateError } = await client.auth.admin.updateUserById(worker.user_id, {
      password: newPassword
    });

    if (updateError) throw new Error(updateError.message);

    // Update password_shown flag
    await this.updateWorker(workerId, { password_shown: false });

    return newPassword;
  }

  /**
   * Deactivate worker
   */
  async deactivateWorker(workerId: string): Promise<WorkerProfile> {
    return this.updateWorker(workerId, { status: 'inactive' });
  }

  /**
   * Suspend worker
   */
  async suspendWorker(workerId: string): Promise<WorkerProfile> {
    return this.updateWorker(workerId, { status: 'suspended' });
  }

  /**
   * Reactivate worker
   */
  async reactivateWorker(workerId: string): Promise<WorkerProfile> {
    return this.updateWorker(workerId, { status: 'active' });
  }

  /**
   * Delete worker (soft delete)
   */
  async deleteWorker(workerId: string): Promise<void> {
    const worker = await this.getWorker(workerId);
    
    // Delete auth user
    const client = await this.supabase.getSupabaseClient();
    await client.auth.admin.deleteUser(worker.user_id);

    // Soft delete worker profile
    await this.updateWorker(workerId, { status: 'inactive' });
  }

  /**
   * Get all workers for a farm (Promise-based version for backward compatibility)
   */
  async getWorkers(farmId: string): Promise<FarmWorker[]> {
    try {
      const client = await this.supabase.getSupabaseClient();
      const { data, error } = await client
        .from('farm_workers')
        .select('*')
        .eq('farm_id', farmId)
        .eq('status', 'active')
        .order('hire_date', { ascending: false });

      if (error) throw error;
      
      this.farmWorkers$.next((data || []) as FarmWorker[]);
      return (data || []) as FarmWorker[];
    } catch (error: any) {
      console.error('Error loading farm workers:', error);
      this.error$.next(error.message);
      throw error;
    }
  }

  /**
   * Add new worker to farm
   */
  async addWorker(farmId: string, workerData: any): Promise<FarmWorker> {
    try {
      this.isLoading$.next(true);
      this.error$.next(null);

      const createRequest: WorkerCreateRequest = {
        farm_id: farmId,
        first_name: workerData.first_name || workerData.worker_name?.split(' ')[0] || '',
        last_name: workerData.last_name || workerData.worker_name?.split(' ').pop() || '',
        phone_number: workerData.phone_number || '',
        position: workerData.position || workerData.role || 'Farm Worker',
        contract_type: workerData.contract_type || workerData.employment_type || 'casual',
        hire_date: workerData.hire_date || new Date().toISOString().split('T')[0],
        national_id: workerData.national_id,
        salary: workerData.salary_amount || workerData.salary
      };

      const result = await this.createWorker(createRequest);
      
      // Reload workers list
      await this.getWorkers(farmId);
      
      this.isLoading$.next(false);
      return result.worker as any as FarmWorker;
    } catch (error: any) {
      this.isLoading$.next(false);
      this.error$.next(error.message);
      throw error;
    }
  }

  // ========================================================================
  // ATTENDANCE MANAGEMENT
  // ========================================================================

  /**
   * Record worker attendance
   */
  async recordAttendance(workerId: string, farmId: string, attendance: Omit<WorkerAttendance, 'id'>): Promise<WorkerAttendance> {
    const client = await this.supabase.getSupabaseClient();
    const { data, error } = await client
      .from('worker_attendance')
      .insert({
        worker_id: workerId,
        farm_id: farmId,
        date: attendance['date'],
        status: attendance['status'],
        check_in_time: attendance['check_in_time'] || null,
        check_out_time: attendance['check_out_time'] || null,
        hours_worked: attendance['hours_worked'] || null,
        notes: attendance['notes'] || null
      })
      .select()
      .single();

    if (error) throw new Error(error.message);
    return data as WorkerAttendance;
  }

  /**
   * Get worker attendance history
   */
  async getAttendanceHistory(workerId: string, startDate: string, endDate: string): Promise<WorkerAttendance[]> {
    const client = await this.supabase.getSupabaseClient();
    const { data, error } = await client
      .from('worker_attendance')
      .select('*')
      .eq('worker_id', workerId)
      .gte('date', startDate)
      .lte('date', endDate)
      .order('date', { ascending: false });

    if (error) throw new Error(error.message);
    return (data || []) as WorkerAttendance[];
  }

  /**
   * Get attendance statistics
   */
  async getAttendanceStats(workerId: string, month: string): Promise<any> {
    const startDate = `${month}-01`;
    const endDate = `${month}-31`;

    const attendance = await this.getAttendanceHistory(workerId, startDate, endDate);

    return {
      totalDays: attendance.length,
      presentDays: attendance.filter(a => a.status === 'present').length,
      absentDays: attendance.filter(a => a.status === 'absent').length,
      lateDays: attendance.filter(a => a.status === 'late').length,
      onLeaveDays: attendance.filter(a => a.status === 'on_leave').length,
      attendanceRate: attendance.length > 0 
        ? Math.round((attendance.filter(a => a.status === 'present').length / attendance.length) * 100)
        : 0
    };
  }

  // ========================================================================
  // PAYROLL MANAGEMENT
  // ========================================================================

  /**
   * Create payroll record
   */
  async createPayroll(farmId: string, payroll: Omit<WorkerPayroll, 'id' | 'created_at' | 'updated_at'>): Promise<WorkerPayroll> {
    const client = await this.supabase.getSupabaseClient();
    const { data, error } = await client
      .from('worker_payroll')
      .insert({
        worker_id: payroll['worker_id'],
        farm_id: farmId,
        payroll_period_start: payroll['payroll_period_start'],
        payroll_period_end: payroll['payroll_period_end'],
        base_salary: payroll['base_salary'],
        allowances: payroll['allowances'] || 0,
        deductions: payroll['deductions'] || 0,
        overtime_hours: payroll['overtime_hours'] || 0,
        overtime_rate: payroll['overtime_rate'] || 0,
        gross_salary: payroll['gross_salary'],
        tax: payroll['tax'] || 0,
        net_salary: payroll['net_salary'],
        paid: payroll['paid'] || false
      })
      .select()
      .single();

    if (error) throw new Error(error.message);
    return data as WorkerPayroll;
  }

  /**
   * Get payroll history
   */
  async getPayrollHistory(workerId: string): Promise<WorkerPayroll[]> {
    const client = await this.supabase.getSupabaseClient();
    const { data, error } = await client
      .from('worker_payroll')
      .select('*')
      .eq('worker_id', workerId)
      .order('payroll_period_start', { ascending: false });

    if (error) throw new Error(error.message);
    return (data || []) as WorkerPayroll[];
  }

  /**
   * Mark payroll as paid
   */
  async markPayrollAsPaid(payrollId: string, paymentDate: string): Promise<WorkerPayroll> {
    const client = await this.supabase.getSupabaseClient();
    const { data, error } = await client
      .from('worker_payroll')
      .update({
        paid: true,
        payment_date: paymentDate
      })
      .eq('id', payrollId)
      .select()
      .single();

    if (error) throw new Error(error.message);
    return data as WorkerPayroll;
  }

  // ========================================================================
  // PERFORMANCE MANAGEMENT
  // ========================================================================

  /**
   * Create performance review
   */
  async createPerformanceReview(farmId: string, review: Omit<WorkerPerformance, 'id' | 'created_at'>): Promise<WorkerPerformance> {
    const client = await this.supabase.getSupabaseClient();
    const { data, error } = await client
      .from('worker_performance')
      .insert({
        worker_id: review.worker_id,
        farm_id: farmId,
        evaluation_date: review.evaluation_date,
        evaluated_by: review.evaluated_by,
        category: review.category,
        score: review.score,
        comments: review.comments || null,
        improvement_areas: review.improvement_areas || null,
        strengths: review.strengths || null,
        next_review_date: review.next_review_date || null
      })
      .select()
      .single();

    if (error) throw new Error(error.message);
    return data as WorkerPerformance;
  }

  /**
   * Get performance history
   */
  async getPerformanceHistory(workerId: string): Promise<WorkerPerformance[]> {
    const client = await this.supabase.getSupabaseClient();
    const { data, error } = await client
      .from('worker_performance')
      .select('*')
      .eq('worker_id', workerId)
      .order('evaluation_date', { ascending: false });

    if (error) throw new Error(error.message);
    return (data || []) as WorkerPerformance[];
  }

  /**
   * Get average performance score
   */
  async getPerformanceScore(workerId: string): Promise<number> {
    const client = await this.supabase.getSupabaseClient();
    const { data, error } = await client
      .from('worker_performance')
      .select('score')
      .eq('worker_id', workerId);

    if (error) throw new Error(error.message);

    const scores = (data || []) as { score: number }[];
    if (scores.length === 0) return 0;

    const average = scores.reduce((sum, item) => sum + item.score, 0) / scores.length;
    return Math.round(average * 10) / 10;
  }

  // ========================================================================
  // TASK MANAGEMENT
  // ========================================================================

  /**
   * Assign task to worker
   */
  async assignTask(farmId: string, task: Omit<WorkerTask, 'id' | 'created_at' | 'updated_at'>): Promise<WorkerTask> {
    const client = await this.supabase.getSupabaseClient();
    const { data, error } = await client
      .from('worker_tasks')
      .insert({
        worker_id: task.worker_id,
        farm_id: farmId,
        task_name: task.task_name,
        description: task.description || null,
        task_type: task.task_type,
        assigned_by: task.assigned_by,
        assigned_date: task.assigned_date,
        due_date: task.due_date,
        priority: task.priority,
        status: task.status || 'assigned',
        notes: task.notes || null
      })
      .select()
      .single();

    if (error) throw new Error(error.message);
    return data as WorkerTask;
  }

  /**
   * Get worker tasks
   */
  async getWorkerTasks(workerId: string): Promise<WorkerTask[]> {
    const client = await this.supabase.getSupabaseClient();
    const { data, error } = await client
      .from('worker_tasks')
      .select('*')
      .eq('worker_id', workerId)
      .order('due_date', { ascending: true });

    if (error) throw new Error(error.message);
    return (data || []) as WorkerTask[];
  }

  /**
   * Update task status
   */
  async updateTaskStatus(taskId: string, status: WorkerTask['status']): Promise<WorkerTask> {
    const client = await this.supabase.getSupabaseClient();
    const { data, error } = await client
      .from('worker_tasks')
      .update({
        status,
        completion_date: status === 'completed' ? new Date().toISOString() : null
      })
      .eq('id', taskId)
      .select()
      .single();

    if (error) throw new Error(error.message);
    return data as WorkerTask;
  }

  // ========================================================================
  // STATE OBSERVABLES
  // ========================================================================

  getFarmWorkers$(): Observable<FarmWorker[]> {
    return this.farmWorkers$.asObservable();
  }

  getCurrentWorker$(): Observable<WorkerProfile | null> {
    return this.currentWorker$.asObservable();
  }

  getIsLoading$(): Observable<boolean> {
    return this.isLoading$.asObservable();
  }

  getError$(): Observable<string | null> {
    return this.error$.asObservable();
  }

  // Legacy method names for compatibility
  getWorkers$(): Observable<FarmWorker[]> {
    return this.farmWorkers$.asObservable();
  }
}
