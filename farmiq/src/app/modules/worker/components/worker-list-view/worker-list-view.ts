/**
 * Worker List View Component
 * Display all farm workers for managers
 */

import { Component, Input, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkerManagementService } from '../../../farmer/services/worker-management.service';
import { FarmWorker } from '../../models/worker-profile.models';

@Component({
  selector: 'app-worker-list-view',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="worker-list-view">
      <h3>All Farm Workers</h3>
      <div class="list-controls">
        <input type="text" placeholder="Search workers..." (input)="filterWorkers($event)" class="search-input" />
        <select (change)="filterByRole($event)" class="filter-select">
          <option value="">All Roles</option>
          <option value="farm_manager">Farm Manager</option>
          <option value="field_supervisor">Field Supervisor</option>
          <option value="harvest_staff">Harvest Staff</option>
          <option value="driver">Driver</option>
        </select>
      </div>
      <div class="workers-table">
        <div *ngIf="filteredWorkers.length === 0" class="empty-state">
          No workers found
        </div>
        <div *ngFor="let worker of filteredWorkers" class="worker-row">
          <div class="worker-info">
            <h4>{{ worker.worker_name }}</h4>
            <p class="role">{{ getRoleLabel(worker.role) }}</p>
          </div>
          <div class="worker-contact">
            <p>{{ worker.phone_number }}</p>
            <p>{{ worker.email }}</p>
          </div>
          <div class="worker-employment">
             <p>{{ capitalize(worker.employment_type || '') }}</p>
            <p>Hired: {{ worker.hire_date | date: 'MMM yyyy' }}</p>
          </div>
          <div class="worker-status" [ngClass]="'status-' + worker.status">
            {{ capitalize(worker.status || 'unknown') }}
          </div>
          <button class="btn-view" (click)="viewWorker(worker)">View</button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .worker-list-view {
      padding: 0;
    }

    h3 {
      margin-top: 0;
      margin-bottom: 15px;
      color: #333;
    }

    .list-controls {
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
    }

    .search-input, .filter-select {
      padding: 8px 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
    }

    .search-input {
      flex: 1;
    }

    .workers-table {
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

    .worker-row {
      background: white;
      border: 1px solid #e0e0e0;
      border-radius: 6px;
      padding: 12px;
      display: flex;
      align-items: center;
      gap: 15px;
    }

    .worker-info {
      flex: 1;
      min-width: 150px;
    }

    .worker-info h4 {
      margin: 0 0 5px 0;
      color: #333;
    }

    .worker-info .role {
      margin: 0;
      font-size: 12px;
      color: #999;
    }

    .worker-contact {
      flex: 1;
      min-width: 150px;
    }

    .worker-contact p {
      margin: 3px 0;
      font-size: 13px;
      color: #666;
    }

    .worker-employment {
      flex: 1;
      min-width: 150px;
    }

    .worker-employment p {
      margin: 3px 0;
      font-size: 13px;
      color: #666;
    }

    .worker-status {
      padding: 6px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
      text-transform: uppercase;
    }

    .worker-status.status-active {
      background: #e8f5e9;
      color: #4CAF50;
    }

    .worker-status.status-inactive {
      background: #ffebee;
      color: #f44336;
    }

    .worker-status.status-on_leave {
      background: #fff3e0;
      color: #ff9800;
    }

    .btn-view {
      padding: 6px 12px;
      background: #667eea;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
    }

    .btn-view:hover {
      background: #5568d3;
    }
  `]
})
export class WorkerListViewComponent implements OnInit {
  @Input() canManageWorkers = false;

  private workerService = inject(WorkerManagementService);

  workers: FarmWorker[] = [];
  filteredWorkers: FarmWorker[] = [];

  ngOnInit(): void {
    this.loadWorkers();
  }

  private loadWorkers(): void {
    this.workerService.getWorkers$().subscribe(workers => {
      this.workers = workers;
      this.filteredWorkers = workers;
    });
  }

  filterWorkers(event: Event): void {
    const searchTerm = (event.target as HTMLInputElement).value.toLowerCase();
    this.filteredWorkers = this.workers.filter(w =>
      (w.worker_name || '').toLowerCase().includes(searchTerm) ||
      (w.phone_number || '').toLowerCase().includes(searchTerm) ||
      (w.email || '').toLowerCase().includes(searchTerm)
    );
  }

  filterByRole(event: Event): void {
    const role = (event.target as HTMLSelectElement).value;
    this.filteredWorkers = role
      ? this.workers.filter(w => w.role === role)
      : this.workers;
  }

  viewWorker(worker: FarmWorker): void {
    console.log('Viewing worker:', worker);
    // Navigate to worker detail
  }

  getRoleLabel(role: string): string {
    const roles: { [key: string]: string } = {
      farm_manager: 'Farm Manager',
      field_supervisor: 'Field Supervisor',
      harvest_staff: 'Harvest Staff',
      driver: 'Driver',
    };
    return roles[role] || role;
  }

  capitalize(str: string): string {
    return str.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  }
}
