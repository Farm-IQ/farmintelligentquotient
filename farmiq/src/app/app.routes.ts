import { Routes } from '@angular/router';
import { LandingComponent } from './components/landing/landing';
import { LoginComponent } from './modules/auth/components/auth/login/login';
import { SignupComponent } from './modules/auth/components/auth/signup/signup';
import { AuthCallback } from './modules/auth/components/oauth/auth-callback/auth-callback';
import { ForgotPasswordComponent } from './modules/auth/components/auth/forgot-password/forgot-password';
import { FarmSetupWizardComponent } from './modules/farmer/components/farm-setup-wizard/farm-setup-wizard';
import { authGuard } from './modules/auth/guards/auth-guard';
import { farmiqIdGuard } from './modules/auth/guards/farmiq-id-guard';

// Import role-specific guards from their respective modules
import { farmerGuard } from './modules/farmer/guards';
import { cooperativeGuard } from './modules/cooperative/guards';
import { lenderGuard } from './modules/lender/guards';
import { agentGuard } from './modules/agent/guards';
import { vendorGuard } from './modules/vendor/guards';
import { workerAuthGuard } from './modules/worker/guards';
import { adminGuard } from './modules/admin/guards';

import { FarmgrowChatbotComponent } from './components/farmgrow-chatbot/farmgrow-chatbot';

export const routes: Routes = [
  {
    path: '',
    component: LandingComponent,
    title: 'FarmIQ - Smart Farming Solutions'
  },
  {
    path: 'login',
    component: LoginComponent,
    title: 'Login - FarmIQ'
  },
  {
    path: 'farmgrow',
    canActivate: [authGuard],
    component: FarmgrowChatbotComponent,
    title: 'FarmGrow ChatBot - FarmIQ'
  },
  
  /**
   * Farm Setup Wizard - After OAuth Role Selection
   * Farmers go through this 4-step wizard after selecting 'farmer' role
   * Collects: county, location, farm size, crops, livestock
   */
  {
    path: 'farm-setup-wizard',
    canActivate: [authGuard],
    component: FarmSetupWizardComponent,
    title: 'Farm Setup Wizard - FarmIQ'
  },

  {
    path: 'signup',
    component: SignupComponent,
    title: 'Sign Up - FarmIQ'
  },

  {
    path: 'auth-callback',
    component: AuthCallback,
    title: 'Authenticating - FarmIQ'
  },
  {
    path: 'forgot-password',
    component: ForgotPasswordComponent,
    title: 'Forgot Password - FarmIQ'
  },

  // ============================================================================
  // FARMER ROLE ROUTES
  // ============================================================================
  {
    path: 'farmer',
    canActivate: [farmerGuard],
    loadChildren: () => import('./modules/farmer/farmer-routing-module').then(m => m.FarmerRoutingModule),
    title: 'Farmer Dashboard - FarmIQ'
  },

  // ============================================================================
  // WORKER ROLE ROUTES
  // ============================================================================
  {
    path: 'worker',
    canActivate: [workerAuthGuard],
    loadChildren: () => import('./modules/worker/worker-routing.module').then(m => m.WorkerRoutingModule),
    title: 'Worker Dashboard - FarmIQ'
  },

  {
    path: 'workers',
    canActivate: [workerAuthGuard],
    loadChildren: () => import('./modules/worker/worker-routing.module').then(m => m.WorkerRoutingModule),
    title: 'Worker Dashboard - FarmIQ'
  },

  // ============================================================================
  // COOPERATIVE ROLE ROUTES
  // ============================================================================
  {
    path: 'cooperative',
   // canActivate: [authGuard, cooperativeGuard],
    loadChildren: () => import('./modules/cooperative/cooperative-module').then(m => m.CooperativeModule),
    title: 'Cooperative Dashboard - FarmIQ'
  },

  // ============================================================================
  // LENDER ROLE ROUTES
  // ============================================================================
  {
    path: 'lender',
    //canActivate: [authGuard, lenderGuard],
    loadChildren: () => import('./modules/lender/lender-module').then(m => m.LenderModule),
    title: 'Lender Dashboard - FarmIQ'
  },

  // ============================================================================
  // AGENT ROLE ROUTES
  // ============================================================================
  {
    path: 'agent',
   // canActivate: [authGuard, agentGuard],
    loadChildren: () => import('./modules/agent/agent-module').then(m => m.AgentModule),
    title: 'Agent Dashboard - FarmIQ'
  },

  // ============================================================================
  // VENDOR ROLE ROUTES
  // ============================================================================
  {
    path: 'vendor',
   // canActivate: [authGuard, vendorGuard],
    loadChildren: () => import('./modules/vendor/vendor-module-module').then(m => m.VendorModuleModule),
    title: 'Vendor Dashboard - FarmIQ'
  },

  // ============================================================================
  // ADMIN ROLE ROUTES
  // ============================================================================
  {
    path: 'admin',
 //   canActivate: [authGuard, adminGuard],
    loadChildren: () => import('./modules/admin/admin-module').then(m => m.AdminModule),
    title: 'Admin Dashboard - FarmIQ'
  },

  {
    path: '**',
    component: LandingComponent
  }
];
