import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { SupabaseService } from '../../services/core/supabase.service';
import { ErrorHandlingService, ErrorType } from '../../services/core/error-handling.service';

/**
 * CORE ERROR INTERCEPTOR
 * Global HTTP error handling for all API requests
 * 
 * Responsibilities:
 * - Transform HTTP errors to user-friendly messages
 * - Handle 401 Unauthorized (expired token)
 * - Handle 403 Forbidden (access denied)
 * - Handle network errors (status 0)
 * - Log errors for debugging
 * 
 * This interceptor runs for ALL HTTP errors before they reach the application
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const errorHandlingService = inject(ErrorHandlingService);
  const supabaseService = inject(SupabaseService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      // Handle the error
      const appError = errorHandlingService.handleError(error, ErrorType.HTTP);

      // Special handling for 401 Unauthorized (auth token expired or invalid)
      if (error.status === 401) {
        console.warn('🔐 Unauthorized request detected. Attempting token refresh...');

        // Clear current session and redirect to login
        // This will be handled by the auth guard
        supabaseService.signOut().catch(err => {
          console.error('Error signing out:', err);
        });
      }

      // Special handling for 403 Forbidden
      if (error.status === 403) {
        console.warn('🚫 Access denied (403)');
      }

      // Special handling for network errors (status 0)
      if (error.status === 0) {
        console.error('🌐 Network error detected');
      }

      // Return the error with user-friendly message
      return throwError(() => appError);
    })
  );
};
