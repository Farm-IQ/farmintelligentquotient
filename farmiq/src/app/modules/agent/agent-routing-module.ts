import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AgentLayout } from './components/agent-layout/agent-layout';
import { AgentOnboardingComponent } from './components/agent-onboarding/agent-onboarding';
import { AgentVerificationComponent } from './components/agent-verification/agent-verification';
import { AgentReportsComponent } from './components/agent-reports/agent-reports';
import { AgentWalletComponent } from './components/agent-wallet/agent-wallet';

const routes: Routes = [
  {
    path: '',
    component: AgentLayout,
    children: [
      {
        path: '',
        component: AgentOnboardingComponent,
        title: 'Dashboard - Agent'
      },
      {
        path: 'verification',
        component: AgentVerificationComponent,
        title: 'Verification - Agent'
      },
      {
        path: 'reports',
        component: AgentReportsComponent,
        title: 'Reports - Agent'
      },
      {
        path: 'wallet',
        component: AgentWalletComponent,
        title: 'Wallet - Agent'
      }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AgentRoutingModule { }
