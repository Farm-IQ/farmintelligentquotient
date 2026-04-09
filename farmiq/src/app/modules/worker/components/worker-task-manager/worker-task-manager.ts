/**
 * Worker Task Manager Component
 * Assign and track worker tasks
 */

import { Component, Input, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { WorkerManagementService } from '../../../farmer/services/worker-management.service';
import { FarmWorker, WorkerTask } from '../../models/worker-profile.models';

@Component({
  selector: 'app-worker-task-manager',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="task-manager">
      <div class="task-header">
        <h3>Task Management</h3>
        <button *ngIf="canManageTasks" (click)="toggleAddTask()" class="btn-primary">
          {{ showAddTask ? 'Cancel' : '+ Assign Task' }}
        </button>
      </div>

      <!-- Add Task Form -->
      <div *ngIf="showAddTask && canManageTasks" class="add-task-form">
        <form [formGroup]="taskForm" (ngSubmit)="assignTask()">
          <div class="form-group">
            <label>Task Title</label>
            <input type="text" formControlName="task_title" placeholder="Enter task title" />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea formControlName="description" rows="3"></textarea>
          </div>
          <div class="form-grid">
            <div class="form-group">
              <label>Due Date</label>
              <input type="date" formControlName="due_date" />
            </div>
            <div class="form-group">
              <label>Priority</label>
              <select formControlName="priority">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
          </div>
          <button type="submit" [disabled]="!taskForm.valid || isLoading" class="btn-success">
            {{ isLoading ? 'Assigning...' : 'Assign Task' }}
          </button>
        </form>
      </div>

      <!-- Task Statistics -->
      <div class="task-stats">
        <div class="stat">
          <label>Total Tasks</label>
          <div class="value">{{ workerTasks.length }}</div>
        </div>
        <div class="stat">
          <label>Pending</label>
          <div class="value">{{ pendingCount }}</div>
        </div>
        <div class="stat">
          <label>In Progress</label>
          <div class="value">{{ inProgressCount }}</div>
        </div>
        <div class="stat">
          <label>Completed</label>
          <div class="value">{{ completedCount }}</div>
        </div>
      </div>

      <!-- Task List -->
      <div class="task-list">
        <div *ngIf="workerTasks.length === 0" class="empty-state">
          No tasks assigned yet
        </div>
        <div *ngFor="let task of workerTasks" class="task-card" [ngClass]="'priority-' + task.priority">
          <div class="task-header-row">
            <h4>Task</h4>
            <span class="status-badge" [ngClass]="'status-' + task.status">
              {{ capitalize(task.status) }}
            </span>
          </div>
          <p class="description">{{ task.description }}</p>
          <div class="task-footer">
            <span class="due-date">Due: {{ task.due_date | date: 'MMM d, y' }}</span>
            <span class="priority-badge" [ngClass]="'priority-' + task.priority">
              {{ capitalize(task.priority || '') }}
            </span>
            <div class="task-actions" *ngIf="!canManageTasks || selectedWorker?.id !== task.worker_id">
              <button (click)="updateTaskStatus(task, 'in_progress')" 
                      *ngIf="task.status === 'assigned'" class="btn-small">
                Start
              </button>
              <button (click)="updateTaskStatus(task, 'completed')" 
                      *ngIf="task.status === 'in_progress'" class="btn-small">
                Complete
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .task-manager {
      padding: 0;
    }

    .task-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }

    .task-header h3 {
      margin: 0;
      color: #333;
    }

    .btn-primary {
      background: #667eea;
      color: white;
      padding: 8px 16px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
    }

    .btn-primary:hover {
      background: #5568d3;
    }

    .add-task-form {
      background: #f9f9f9;
      padding: 15px;
      border-radius: 6px;
      margin-bottom: 20px;
      border: 1px solid #e0e0e0;
    }

    .form-group {
      margin-bottom: 12px;
    }

    .form-group label {
      display: block;
      margin-bottom: 5px;
      font-weight: 500;
      color: #555;
      font-size: 13px;
    }

    .form-group input,
    .form-group textarea,
    .form-group select {
      width: 100%;
      padding: 8px 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
    }

    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    .btn-success {
      background: #4CAF50;
      color: white;
      padding: 8px 16px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 500;
    }

    .btn-success:hover {
      background: #45a049;
    }

    .task-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
      gap: 12px;
      margin-bottom: 20px;
    }

    .stat {
      background: #f5f5f5;
      padding: 12px;
      border-radius: 6px;
      text-align: center;
    }

    .stat label {
      font-size: 12px;
      color: #999;
      display: block;
      margin-bottom: 5px;
    }

    .stat .value {
      font-size: 20px;
      font-weight: bold;
      color: #333;
    }

    .task-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .empty-state {
      text-align: center;
      padding: 40px;
      color: #999;
      background: #f5f5f5;
      border-radius: 4px;
    }

    .task-card {
      background: white;
      border: 1px solid #e0e0e0;
      border-left: 4px solid #ddd;
      border-radius: 6px;
      padding: 12px;
    }

    .task-card.priority-high {
      border-left-color: #f44336;
    }

    .task-card.priority-urgent {
      border-left-color: #d32f2f;
      background: #fff5f5;
    }

    .task-card.priority-medium {
      border-left-color: #ff9800;
    }

    .task-card.priority-low {
      border-left-color: #4CAF50;
    }

    .task-header-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }

    .task-header-row h4 {
      margin: 0;
      color: #333;
      font-size: 15px;
    }

    .status-badge {
      padding: 3px 8px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 500;
      text-transform: uppercase;
    }

    .status-badge.status-pending {
      background: #fff3e0;
      color: #ff9800;
    }

    .status-badge.status-in_progress {
      background: #e3f2fd;
      color: #1976d2;
    }

    .status-badge.status-completed {
      background: #e8f5e9;
      color: #4CAF50;
    }

    .description {
      margin: 8px 0;
      font-size: 13px;
      color: #666;
    }

    .task-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      font-size: 12px;
    }

    .due-date {
      color: #999;
    }

    .priority-badge {
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 500;
      text-transform: uppercase;
    }

    .priority-badge.priority-high {
      background: #ffebee;
      color: #f44336;
    }

    .priority-badge.priority-urgent {
      background: #ffcdd2;
      color: #d32f2f;
    }

    .priority-badge.priority-medium {
      background: #fff3e0;
      color: #ff9800;
    }

    .priority-badge.priority-low {
      background: #e8f5e9;
      color: #4CAF50;
    }

    .task-actions {
      display: flex;
      gap: 6px;
    }

    .btn-small {
      padding: 4px 8px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 11px;
      cursor: pointer;
      background: white;
      color: #333;
    }

    .btn-small:hover {
      background: #f0f0f0;
    }
  `]
})
export class WorkerTaskManagerComponent implements OnInit {
  @Input() selectedWorker: FarmWorker | null = null;
  @Input() farmId: string = '';
  @Input() canManageTasks = false;

  private fb = inject(FormBuilder);
  private workerService = inject(WorkerManagementService);

  taskForm!: FormGroup;
  workerTasks: WorkerTask[] = [];
  showAddTask = false;
  isLoading = false;

  get pendingCount(): number {
    return this.workerTasks.filter(t => t.status === 'assigned').length;
  }

  get inProgressCount(): number {
    return this.workerTasks.filter(t => t.status === 'in_progress').length;
  }

  get completedCount(): number {
    return this.workerTasks.filter(t => t.status === 'completed').length;
  }

  ngOnInit(): void {
    this.initializeForm();
    this.loadTasks();
  }

  private initializeForm(): void {
    this.taskForm = this.fb.group({
      task_title: ['', [Validators.required]],
      description: [''],
      due_date: ['', [Validators.required]],
      priority: ['medium', [Validators.required]],
    });
  }

  private loadTasks(): void {
    if (!this.selectedWorker) return;

    this.workerService.getWorkerTasks(this.selectedWorker.id)
      .then(tasks => {
        this.workerTasks = tasks;
      })
      .catch(err => console.error('Failed to load tasks:', err));
  }

  toggleAddTask(): void {
    this.showAddTask = !this.showAddTask;
    if (!this.showAddTask) {
      this.taskForm.reset();
    }
  }

  assignTask(): void {
    if (!this.selectedWorker || !this.taskForm.valid) return;

    this.isLoading = true;
    const formValue = this.taskForm.value;
    const task: Omit<WorkerTask, 'id' | 'createdAt' | 'updatedAt'> = {
      worker_id: this.selectedWorker.id,
      farm_id: this.farmId,
      task_name: formValue.task_title,
      description: formValue.description,
      task_type: 'routine',
      assigned_by: '', // Will be set from auth context
      assigned_date: new Date().toISOString().split('T')[0],
      due_date: formValue.due_date,
      priority: formValue.priority,
      status: 'assigned',
      notes: formValue.description,
    };

    this.workerService.assignTask(this.farmId, task as any)
      .then(() => {
        this.toggleAddTask();
        this.loadTasks();
        this.isLoading = false;
      })
      .catch(err => {
        console.error('Failed to assign task:', err);
        this.isLoading = false;
      });
  }

  updateTaskStatus(task: WorkerTask, newStatus: string): void {
    this.workerService.updateTaskStatus(task.id, newStatus as WorkerTask['status'])
      .then(() => {
        this.loadTasks();
      })
      .catch(err => console.error('Failed to update task:', err));
  }

  capitalize(str: string): string {
    return str.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  }
}
