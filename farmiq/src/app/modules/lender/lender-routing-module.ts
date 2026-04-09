import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LenderLayout } from './components/lender-layout/lender-layout';
import { LenderRiskDashboardComponent } from './components/lender-risk-dashboard/lender-risk-dashboard';
import { LenderLoanDecisionComponent } from './components/lender-loan-decision/lender-loan-decision';
import { LenderInsightsComponent } from './components/lender-insights/lender-insights';
import { LenderPortfolioMonitoringComponent } from './components/lender-portfolio-monitoring/lender-portfolio-monitoring';
import { LenderWalletComponent } from './components/lender-wallet/lender-wallet';

const routes: Routes = [
  {
    path: '',
    component: LenderLayout,
    children: [
      {
        path: '',
        component: LenderRiskDashboardComponent,
        title: 'Risk Dashboard - Lender'
      },
      {
        path: 'loan-decision',
        component: LenderLoanDecisionComponent,
        title: 'Loan Decision - Lender'
      },
      {
        path: 'insights',
        component: LenderInsightsComponent,
        title: 'Insights Marketplace - Lender'
      },
      {
        path: 'portfolio',
        component: LenderPortfolioMonitoringComponent,
        title: 'Portfolio Monitoring - Lender'
      },
      {
        path: 'wallet',
        component: LenderWalletComponent,
        title: 'Wallet - Lender'
      }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class LenderRoutingModule { }
