/**
 * Core Services - Central Export
 * Provides core, low-level services used across the entire application
 * 
 * These services are application-level and can be used by any module:
 * - SupabaseService: Database and authentication backend
 * - ErrorHandlingService: Error transformation and logging
 * - FarmiqIdService: Unique identifier generation
 * 
 * Usage:
 * ```typescript
 * import { SupabaseService } from 'src/app/services/core';
 * import { ErrorHandlingService } from 'src/app/services/core';
 * ```
 */

// Core utilities
export { SupabaseService } from './supabase.service';
export { ErrorHandlingService, ErrorType, ErrorSeverity } from './error-handling.service';
export { FarmiqIdService } from './farmiq-id.service';

// Re-export error types for convenience
export type { AppError } from './error-handling.service';
