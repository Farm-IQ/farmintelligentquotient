import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { FarmerLayoutComponent } from './components/farmer-layout/farmer-layout';
import { FarmerDashboardComponent } from './components/farmer-dashboard/farmer-dashboard';
import { FarmerCreditScoreComponent } from './components/farmer-credit-score/farmer-credit-score';
import { FarmerAnalyticsComponent } from './components/farmer-analytics/farmer-analytics';
import { FarmerWalletComponent } from './components/farmer-wallet/farmer-wallet';
import { FarmerSettingsComponent } from './components/farmer-settings/farmer-settings';
import { FarmerAccountComponent } from './components/farmer-account/farmer-account';
import { FarmerMarketInsightsComponent } from './components/farmer-market-insights/farmer-market-insights';
import { FarmSetupWizardComponent } from './components/farm-setup-wizard/farm-setup-wizard';
// import { WorkerDashboardComponent } from './components/worker-dashboard/worker-dashboard';
import { WorkerManagementComponent } from '../worker/components/worker-management/worker-management';
import { WorkerAttendanceTrackerComponent } from '../worker/components/worker-attendance-tracker/worker-attendance-tracker';
import { WorkerPayrollManagerComponent } from '../worker/components/worker-payroll-manager/worker-payroll-manager';
import { WorkerPerformanceTrackerComponent } from '../worker/components/worker-performance-tracker/worker-performance-tracker';
import { WorkerTaskManagerComponent } from '../worker/components/worker-task-manager/worker-task-manager';
// import { WorkerListViewComponent } from './components/worker-list-view/worker-list-view';
import { WorkerEquipmentManagerComponent } from '../worker/components/worker-equipment-manager/worker-equipment-manager';
import { WorkerAnalyticsComponent } from '../worker/components/worker-analytics/worker-analytics';

const routes: Routes = [
  {
    path: 'setup',
    component: FarmSetupWizardComponent,
    title: 'Farm Setup - FarmIQ'
  },
  {
    path: '',
    component: FarmerLayoutComponent,
    children: [
      {
        path: '',
        component: FarmerDashboardComponent,
        title: 'Dashboard - FarmIQ'
      },
      {
        path: 'analytics',
        component: FarmerAnalyticsComponent,
        title: 'Analytics - FarmIQ'
      },
      {
        path: 'credit-score',
        component: FarmerCreditScoreComponent,
        title: 'Credit Score - FarmIQ'
      },
      {
        path: 'wallet',
        component: FarmerWalletComponent,
        title: 'Wallet - FarmIQ'
      },
      {
        path: 'market-insights',
        component: FarmerMarketInsightsComponent,
        title: 'FarmSuite Insights - FarmIQ'
      },
      {
        path: 'settings',
        component: FarmerSettingsComponent,
        title: 'Settings - FarmIQ'
      },
      {
        path: 'account',
        component: FarmerAccountComponent,
        title: 'Account - FarmIQ'
      },
      // TODO: Uncomment once WorkerDashboardComponent and WorkerListViewComponent are created
      /*
      {
        path: 'workers',
        component: WorkerDashboardComponent,
        title: 'Worker Management - FarmIQ',
        children: [
          {
            path: 'dashboard',
            component: WorkerDashboardComponent,
            title: 'Dashboard - FarmIQ'
          },
          {
            path: 'management',
            component: WorkerManagementComponent,
            title: 'Worker Management - FarmIQ'
          },
          {
            path: 'attendance',
            component: WorkerAttendanceTrackerComponent,
            title: 'Attendance Tracking - FarmIQ'
          },
          {
            path: 'payroll',
            component: WorkerPayrollManagerComponent,
            title: 'Payroll Management - FarmIQ'
          },
          {
            path: 'performance',
            component: WorkerPerformanceTrackerComponent,
            title: 'Performance Tracking - FarmIQ'
          },
          {
            path: 'tasks',
            component: WorkerTaskManagerComponent,
            title: 'Task Management - FarmIQ'
          },
          {
            path: 'list',
            component: WorkerListViewComponent,
            title: 'Worker List - FarmIQ'
          },
          {
            path: 'analytics',
            component: WorkerAnalyticsComponent,
            title: 'Worker Analytics - FarmIQ'
          },
          {
            path: 'equipment',
            component: WorkerEquipmentManagerComponent,
            title: 'Equipment Management - FarmIQ'
          }
        ]
      }
      */
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class FarmerRoutingModule { }
