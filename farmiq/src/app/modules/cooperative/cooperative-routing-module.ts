import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { CooperativeLayout } from './components/cooperative-layout/cooperative-layout';
import { CooperativeDashboardComponent } from './components/cooperative-dashboard/cooperative-dashboard';
import { CooperativeMemberManagementComponent } from './components/cooperative-member-management/cooperative-member-management';
import { CooperativeInsightsComponent } from './components/cooperative-insights/cooperative-insights';
import { CooperativeBulkCreditToolComponent } from './components/cooperative-bulk-credit-tool/cooperative-bulk-credit-tool';
import { CooperativeFinanceComponent } from './components/cooperative-finance/cooperative-finance';
import { CooperativeWalletComponent } from './components/cooperative-wallet/cooperative-wallet';

const routes: Routes = [
  {
    path: '',
    component: CooperativeLayout,
    children: [
      {
        path: '',
        component: CooperativeDashboardComponent,
        title: 'Dashboard - Cooperative'
      },
      {
        path: 'members',
        component: CooperativeMemberManagementComponent,
        title: 'Member Management - Cooperative'
      },
      {
        path: 'insights',
        component: CooperativeInsightsComponent,
        title: 'Insights Marketplace - Cooperative'
      },
      {
        path: 'bulk-credit-tool',
        component: CooperativeBulkCreditToolComponent,
        title: 'Bulk Credit Tool - Cooperative'
      },
      {
        path: 'finance',
        component: CooperativeFinanceComponent,
        title: 'Finance Dashboard - Cooperative'
      },
      {
        path: 'wallet',
        component: CooperativeWalletComponent,
        title: 'Wallet - Cooperative'
      }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class CooperativeRoutingModule { }
