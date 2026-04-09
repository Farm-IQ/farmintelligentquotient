/**
 * Auth Module Services - Central Export
 * Single point of import for all auth-related services
 * 
 * Organization:
 * - Core services: SupabaseService, ErrorHandlingService, FarmiqIdService (re-exported from core)
 * - Auth management: AuthRoleService, OAuthService, RoleService
 * - Email validation: EmailValidationService
 * - Security: RateLimitService
 * 
 * Backward Compatibility:
 * Services previously in auth module are now in services/core but re-exported here
 * Existing imports like "import { SupabaseService } from '@auth/services'" continue to work
 * 
 * Usage:
 * ```typescript
 * // Old import style (still works via re-export)
 * import { SupabaseService } from '@auth/services';
 * 
 * // New import style (recommended - direct from core)
 * import { SupabaseService } from 'src/app/services/core';
 * ```
 */

// ============================================================================
// RE-EXPORTS FROM CORE SERVICES (for backward compatibility)
// ============================================================================
export { SupabaseService } from '../../../services/core/supabase.service';
export { ErrorHandlingService, ErrorType, ErrorSeverity } from '../../../services/core/error-handling.service';
export { FarmiqIdService } from '../../../services/core/farmiq-id.service';

// ============================================================================
// AUTH-SPECIFIC SERVICES (remain in auth module)
// ============================================================================
export { RateLimitService } from './rate-limit.service';

// Auth management services
export { AuthRoleService } from './auth-role';
export { OAuthService } from './oauth.service';
export { EmailValidationService } from './email-validation.service';
export { RoleService } from './role';
