/**
 * Worker Module Routing
 * Handles all worker-related routes with authentication
 */

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { WorkerLayoutComponent } from './components/worker-layout/worker-layout';
import { workerAuthGuard } from './guards/worker-auth.guard';

// Import worker components
import { WorkerManagementComponent } from './components/worker-management/worker-management';
import { WorkerAttendanceTrackerComponent } from './components/worker-attendance-tracker/worker-attendance-tracker';
import { WorkerPayrollManagerComponent } from './components/worker-payroll-manager/worker-payroll-manager';
import { WorkerPerformanceTrackerComponent } from './components/worker-performance-tracker/worker-performance-tracker';
import { WorkerTaskManagerComponent } from './components/worker-task-manager/worker-task-manager';
import { WorkerAnalyticsComponent } from './components/worker-analytics/worker-analytics';
import { WorkerEquipmentManagerComponent } from './components/worker-equipment-manager/worker-equipment-manager';
import { WorkerProfileComponent } from './components/worker-profile/worker-profile';
import { WorkerListViewComponent } from './components/worker-list-view/worker-list-view';
import { WorkerDashboardComponent } from './components/worker-dashboard/worker-dashboard';

const routes: Routes = [
  {
    path: '',
    component: WorkerLayoutComponent,
    //canActivate: [workerAuthGuard],
    children: [
      // TODO: Uncomment once WorkerDashboardComponent is created
      
      {
        path: 'dashboard',
        component: WorkerDashboardComponent,
        title: 'Dashboard - FarmIQ'
      },
      
      {
        path: 'attendance',
        component: WorkerAttendanceTrackerComponent,
        title: 'Attendance - FarmIQ'
      },
      {
        path: 'tasks',
        component: WorkerTaskManagerComponent,
        title: 'Tasks - FarmIQ'
      },
      {
        path: 'payroll',
        component: WorkerPayrollManagerComponent,
        title: 'Payroll - FarmIQ'
      },
      {
        path: 'performance',
        component: WorkerPerformanceTrackerComponent,
        title: 'Performance - FarmIQ'
      },
      {
        path: 'equipment',
        component: WorkerEquipmentManagerComponent,
        title: 'Equipment - FarmIQ'
      },
      {
        path: 'analytics',
        component: WorkerAnalyticsComponent,
        title: 'Analytics - FarmIQ'
      },
      // TODO: Uncomment once WorkerListViewComponent is created
      {
        path: 'management',
        component: WorkerManagementComponent,
        title: 'Management - FarmIQ'
      },
      {
        path: 'list',
        component: WorkerListViewComponent,
        title: 'Worker List - FarmIQ'
      },
      
      {
        path: 'profile',
        component: WorkerProfileComponent,
        title: 'Profile - FarmIQ'
      },
      {
        path: 'change-password',
        component: WorkerProfileComponent,
        title: 'Change Password - FarmIQ'
      },
      {
        path: '',
        redirectTo: 'profile',
        pathMatch: 'full'
      }
    ]
  },
  {
    path: '',
    redirectTo: 'profile',
    pathMatch: 'full'
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class WorkerRoutingModule { }
