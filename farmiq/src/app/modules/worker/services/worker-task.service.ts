/**
 * Worker Task Service
 * Handles task assignment, tracking, and completion
 */

import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';

export interface WorkTask {
  id: string;
  assignedTo: string;
  assignedBy: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category: string;
  location?: string;
  startDate: string;
  dueDate: string;
  estimatedDuration?: number; // in hours
  actualDuration?: number; // in hours
  status: 'assigned' | 'in_progress' | 'completed' | 'overdue' | 'cancelled';
  completionDate?: string;
  completionNotes?: string;
  attachments?: string[];
}

export interface TaskMetrics {
  workerId: string;
  totalAssigned: number;
  completed: number;
  inProgress: number;
  overdue: number;
  cancelled: number;
  completionRate: number; // percentage
  avgCompletionTime: number; // in hours
}

@Injectable({ providedIn: 'root' })
export class WorkerTaskService {
  private apiUrl = environment.apiUrl;
  private supabaseUrl = `${environment.supabase.url}/rest/v1`;

  // ========== STATE ==========
  tasks = signal<WorkTask[]>([]);
  assignedTasks = signal<WorkTask[]>([]);
  taskMetrics = signal<TaskMetrics | null>(null);
  loading = signal<boolean>(false);
  error = signal<string | null>(null);

  // ========== COMPUTED ==========
  activeTasks = computed(() => {
    return this.tasks().filter(t => 
      t.status === 'assigned' || t.status === 'in_progress'
    );
  });

  overdueTasks = computed(() => {
    const now = new Date();
    return this.tasks().filter(t => {
      if (t.status === 'overdue') return true;
      if (t.status !== 'completed' && t.status !== 'cancelled') {
        return new Date(t.dueDate) < now;
      }
      return false;
    });
  });

  completedToday = computed(() => {
    const today = new Date().toISOString().split('T')[0];
    return this.tasks().filter(t => 
      t.status === 'completed' && 
      t.completionDate?.startsWith(today)
    ).length;
  });

  constructor(private http: HttpClient) {}

  /**
   * Get tasks for a worker
   */
  getWorkerTasks(workerId: string, status?: WorkTask['status']): Observable<WorkTask[]> {
    this.loading.set(true);
    let url = `${this.supabaseUrl}/farm_tasks?assigned_to=eq.${workerId}&order=due_date.asc`;
    if (status) url += `&status=eq.${status}`;

    return this.http.get<WorkTask[]>(
      url,
      { headers: this.getHeaders() }
    ).pipe(
      tap((tasksData: WorkTask[]) => {
        this.assignedTasks.set(tasksData);
        this.loading.set(false);
      }),
      catchError((err) => this.handleError('Failed to fetch tasks', err))
    );
  }

  /**
   * Get all farm tasks (for supervisors)
   */
  getFarmTasks(farmId: string): Observable<WorkTask[]> {
    this.loading.set(true);
    return this.http.get<WorkTask[]>(
      `${this.supabaseUrl}/farm_tasks?farm_id=eq.${farmId}&order=due_date.asc`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((tasksData: WorkTask[]) => {
        this.tasks.set(tasksData);
        this.loading.set(false);
      }),
      catchError((err) => this.handleError('Failed to fetch farm tasks', err))
    );
  }

  /**
   * LOGIC: Create and assign a task
   * Validates dates and priority
   */
  createTask(
    farmId: string,
    assignedTo: string,
    assignedBy: string,
    task: Partial<WorkTask>
  ): Observable<WorkTask> {
    // Validate dates
    const startDate = new Date(task.startDate!);
    const dueDate = new Date(task.dueDate!);

    if (dueDate < startDate) {
      return throwError(() => new Error('Due date must be after start date'));
    }

    const payload = {
      farm_id: farmId,
      assigned_to: assignedTo,
      assigned_by: assignedBy,
      title: task.title,
      description: task.description,
      priority: task.priority || 'medium',
      category: task.category,
      location: task.location,
      start_date: task.startDate,
      due_date: task.dueDate,
      estimated_duration: task.estimatedDuration,
      status: 'assigned',
      attachments: task.attachments || []
    };

    return this.http.post<WorkTask>(
      `${this.supabaseUrl}/farm_tasks`,
      payload,
      { headers: this.getHeaders() }
    ).pipe(
      tap((newTask: WorkTask) => {
        const updated = [...this.tasks(), newTask];
        this.tasks.set(updated);
      }),
      catchError((err) => this.handleError('Failed to create task', err))
    );
  }

  /**
   * Update task status (workflow)
   */
  updateTaskStatus(taskId: string, status: WorkTask['status']): Observable<WorkTask> {
    const payload: any = { status };
    
    // If marking as completed, add completion info
    if (status === 'completed') {
      payload.completion_date = new Date().toISOString();
    }

    // If task was overdue and now completed, mark completion date
    if (status === 'overdue') {
      const now = new Date();
      payload.status = 'in_progress'; // Overdue status is auto-managed
    }

    return this.http.patch<WorkTask>(
      `${this.supabaseUrl}/farm_tasks?id=eq.${taskId}`,
      payload,
      { headers: this.getHeaders() }
    ).pipe(
      tap((updated: WorkTask) => {
        const tasks = this.tasks().map(t => t.id === taskId ? updated : t);
        this.tasks.set(tasks);
      }),
      catchError((err) => this.handleError('Failed to update task', err))
    );
  }

  /**
   * Complete a task with notes
   */
  completeTask(taskId: string, completionNotes: string, actualDuration?: number): Observable<WorkTask> {
    return this.updateTaskStatus(taskId, 'completed').pipe(
      switchMap((task) => {
        const payload = {
          completion_notes: completionNotes,
          actual_duration: actualDuration
        };

        return this.http.patch<WorkTask>(
          `${this.supabaseUrl}/farm_tasks?id=eq.${taskId}`,
          payload,
          { headers: this.getHeaders() }
        );
      }),
      catchError((err) => this.handleError('Failed to complete task', err))
    );
  }

  /**
   * LOGIC: Auto-update task status based on dates
   * Called periodically to mark tasks as overdue
   */
  updateOverdueTasks(): void {
    const now = new Date();
    const tasks = this.tasks();

    tasks.forEach(task => {
      if (
        task.status !== 'completed' && 
        task.status !== 'cancelled' && 
        new Date(task.dueDate) < now
      ) {
        this.http.patch(
          `${this.supabaseUrl}/farm_tasks?id=eq.${task.id}`,
          { status: 'overdue' },
          { headers: this.getHeaders() }
        ).subscribe();
      }
    });
  }

  /**
   * Get task metrics for a worker
   */
  getTaskMetrics(workerId: string): Observable<TaskMetrics> {
    return this.http.get<TaskMetrics>(
      `${this.apiUrl}/workers/${workerId}/task-metrics`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((metrics: TaskMetrics) => {
        this.taskMetrics.set(metrics);
      }),
      catchError((err) => this.handleError('Failed to fetch metrics', err))
    );
  }

  /**
   * Bulk assign tasks to multiple workers
   */
  bulkAssignTasks(farmId: string, workerIds: string[], task: Partial<WorkTask>, assignedBy: string): Observable<WorkTask[]> {
    const tasks = workerIds.map(workerId => 
      this.createTask(farmId, workerId, assignedBy, task)
    );

    return combineLatest(tasks).pipe(
      catchError((err) => this.handleError('Failed to bulk assign tasks', err))
    );
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

// Add missing imports
import { switchMap } from 'rxjs/operators';
import { combineLatest } from 'rxjs';
