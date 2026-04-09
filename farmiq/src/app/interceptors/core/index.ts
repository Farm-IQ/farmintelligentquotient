/**
 * CORE INTERCEPTORS - Central Export
 * Global HTTP interceptors for all API requests
 * 
 * These interceptors run for ALL HTTP requests in the entire application
 * 
 * Usage in app.config.ts:
 * ```typescript
 * import { apiInterceptor, errorInterceptor } from './interceptors/core';
 * 
 * provideHttpClient(
 *   withFetch(),
 *   withInterceptors([apiInterceptor, errorInterceptor])
 * )
 * ```
 * 
 * Order matters:
 * 1. apiInterceptor (adds auth headers)
 * 2. errorInterceptor (handles errors)
 */

export { apiInterceptor } from './api-interceptor';
export { errorInterceptor } from './error-interceptor';
