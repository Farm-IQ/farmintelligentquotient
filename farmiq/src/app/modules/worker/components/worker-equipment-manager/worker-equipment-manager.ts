/**
 * Worker Equipment Manager Component
 * Manage equipment access and assignments for drivers/operators
 */

import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FarmWorker } from '../../models/worker-profile.models';

@Component({
  selector: 'app-worker-equipment-manager',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="equipment-manager">
      <h3>Equipment Management</h3>
      <p class="info">Manage equipment access and assignments for {{ selectedWorker?.worker_name }}</p>
      
      <div class="equipment-section">
        <h4>Assigned Equipment</h4>
        <div class="equipment-list">
          <div class="equipment-card">
            <div class="equipment-name">Tractor A45</div>
            <div class="equipment-status assigned">Assigned</div>
          </div>
          <div class="equipment-card">
            <div class="equipment-name">Spray Equipment SP-100</div>
            <div class="equipment-status assigned">Assigned</div>
          </div>
        </div>
      </div>

      <div class="equipment-section">
        <h4>Available Equipment</h4>
        <div class="equipment-list">
          <div class="equipment-card">
            <div class="equipment-name">Cultivator C-200</div>
            <button class="btn-assign">Assign</button>
          </div>
          <div class="equipment-card">
            <div class="equipment-name">Harvester H-300</div>
            <button class="btn-assign">Assign</button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .equipment-manager {
      padding: 0;
    }

    h3 {
      margin-top: 0;
      margin-bottom: 10px;
      color: #333;
    }

    .info {
      margin: 0 0 20px 0;
      font-size: 13px;
      color: #666;
    }

    .equipment-section {
      margin-bottom: 25px;
    }

    .equipment-section h4 {
      margin-top: 0;
      margin-bottom: 12px;
      color: #555;
      font-size: 14px;
    }

    .equipment-list {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 12px;
    }

    .equipment-card {
      background: white;
      border: 1px solid #e0e0e0;
      border-radius: 6px;
      padding: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .equipment-name {
      font-weight: 500;
      color: #333;
      flex: 1;
    }

    .equipment-status {
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 500;
      text-transform: uppercase;
    }

    .equipment-status.assigned {
      background: #e8f5e9;
      color: #4CAF50;
    }

    .btn-assign {
      padding: 6px 12px;
      background: #667eea;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
    }

    .btn-assign:hover {
      background: #5568d3;
    }
  `]
})
export class WorkerEquipmentManagerComponent {
  @Input() selectedWorker: any;
}
