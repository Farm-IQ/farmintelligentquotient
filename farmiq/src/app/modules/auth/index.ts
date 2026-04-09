/**
 * Auth Module - Root Barrel Export
 * Complete public API for the auth module
 * 
 * Structure:
 * - Components: Login, Register, OAuth signin, MFA setup
 * - Guards: Auth, role-based, permission-based
 * - Services: Core auth, credentials, OAuth, email validation
 * - Interceptors: Token injection, error handling, refresh logic
 * - Models: User profiles, auth state, credentials
 * - Utils: Validators, helpers, constants
 * - Directives: Auth state directives
 * 
 * Usage:
 * ```typescript
 * // In app.routes.ts
 * import { AuthModule, authRoutes, authGuard } from '@auth';
 * 
 * // Routes
 * {
 *   path: 'auth',
 *   loadChildren: () => import('@auth').then(m => m.authRoutes),
 *   canActivate: [authGuard]
 * }
 * 
 * // Individual imports
 * import { LoginComponent, SupabaseService, validateEmail } from '@auth';
 * ```
 * 
 * @module auth
 * @exports AuthModule
 * @exports authRoutes
 * @exports authGuard
 * @exports authRoleGuard
 * @exports SupabaseService
 * @exports User
 * @exports LoginCredentials
 */

// ============================================================================
// GUARDS
// ============================================================================
export { authGuard } from './guards/auth-guard';
export { roleGuard } from './guards/role-guard';

// ============================================================================
// SERVICES
// ============================================================================
export {
  SupabaseService,
  AuthRoleService,
  OAuthService,
  EmailValidationService,
  FarmiqIdService,
  RateLimitService,
  ErrorHandlingService,
  RoleService,
} from './services';

// ============================================================================
// MODELS
// ============================================================================
export type {
  UserRole,
  AuthUser,
  SignUpRequest,
  SignInRequest,
  UpdateProfileRequest,
  LoginRequest,
  LoginResponse,
} from './models';







// ============================================================================
// MODULE CONFIGURATION
// ============================================================================
// Services are exported above and can be provided in app.config.ts

