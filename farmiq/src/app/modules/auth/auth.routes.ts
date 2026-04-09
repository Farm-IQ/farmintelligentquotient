/**
 * Authentication Module Routes
 * Defines all authentication-related routes including:
 * - Login, Signup, Password Reset
 * - OAuth Callback
 * - Protected routes with auth guards
 */

import { Routes } from '@angular/router';

// Import auth components
import { LoginComponent } from './components/auth/login/login';
import { SignupComponent } from './components/auth/signup/signup';
import { ForgotPasswordComponent } from './components/auth/forgot-password/forgot-password';
import { AuthCallback } from './components/oauth/auth-callback/auth-callback';

// Import auth guards (from auth module)
import { authGuard } from './guards/auth-guard';
import { farmiqIdGuard } from './guards/farmiq-id-guard';
import { roleGuard } from './guards/role-guard';

/**
 * Public Authentication Routes
 * These routes are accessible without authentication
 */
export const authRoutes: Routes = [
  {
    path: 'login',
    component: LoginComponent,
    title: 'Login - FarmIQ',
    data: { description: 'User login with email/password or OAuth' }
  },
  {
    path: 'signup',
    component: SignupComponent,
    title: 'Sign Up - FarmIQ',
    data: { description: 'Create new FarmIQ account' }
  },
  {
    path: 'forgot-password',
    component: ForgotPasswordComponent,
    title: 'Forgot Password - FarmIQ',
    data: { description: 'Reset forgotten password via email' }
  },
  {
    path: 'auth-callback',
    component: AuthCallback,
    title: 'Authenticating - FarmIQ',
    data: { description: 'OAuth provider callback handler' }
  }
];

/**
 * Protected Routes (require authentication)
 * Add routes here that require authentication guard
 */
export const protectedAuthRoutes: Routes = [
  // Example: add routes that require authentication
  // {
  //   path: 'dashboard',
  //   canActivate: [authGuard],
  //   component: DashboardComponent,
  //   title: 'Dashboard - FarmIQ'
  // }
];
