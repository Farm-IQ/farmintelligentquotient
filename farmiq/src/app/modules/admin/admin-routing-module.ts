import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AdminLayout } from './components/admin-layout/admin-layout';
import { AdminDashboardComponent } from './components/admin-dashboard/admin-dashboard';
import { AdminUserManagementComponent } from './components/admin-user-management/admin-user-management';
import { AdminDataGovernanceComponent } from './components/admin-data-governance/admin-data-governance';
import { AdminModelOperationsComponent } from './components/admin-model-operations/admin-model-operations';
import { AdminHcsIntegrationComponent } from './components/admin-hcs-integration/admin-hcs-integration';
import { AdminTokenomicsComponent } from './components/admin-tokenomics/admin-tokenomics';
import { AdminPaymentManagementComponent } from './components/admin-payment-management/admin-payment-management';
import { AdminReconciliationComponent } from './components/admin-reconciliation/admin-reconciliation';

const routes: Routes = [
  {
    path: '',
    component: AdminLayout,
    children: [
      {
        path: '',
        component: AdminDashboardComponent,
        title: 'Global Dashboard - Admin'
      },
      {
        path: 'users',
        component: AdminUserManagementComponent,
        title: 'User Management - Admin'
      },
      {
        path: 'data-governance',
        component: AdminDataGovernanceComponent,
        title: 'Data Governance - Admin'
      },
      {
        path: 'model-operations',
        component: AdminModelOperationsComponent,
        title: 'Model Operations - Admin'
      },
      {
        path: 'hcs',
        component: AdminHcsIntegrationComponent,
        title: 'HCS Dashboard - Admin'
      },
      {
        path: 'tokenomics',
        component: AdminTokenomicsComponent,
        title: 'Tokenomics - Admin'
      },
      {
        path: 'payment',
        component: AdminPaymentManagementComponent,
        title: 'Payment Dashboard - Admin'
      },
      {
        path: 'reconciliation',
        component: AdminReconciliationComponent,
        title: 'Reconciliation - Admin'
      }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AdminRoutingModule { }
