import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { SupabaseService } from '../../services/core/supabase.service';

/**
 * CORE API INTERCEPTOR
 * Global HTTP interceptor for all API requests
 * 
 * Responsibilities:
 * - Add JWT token from Supabase to Authorization header
 * - Add X-FarmIQ-ID header for backend routing
 * - Add X-User-Role header for optimization
 * - Set Content-Type application/json
 * 
 * This interceptor runs for ALL HTTP requests before they reach the backend
 */
export const apiInterceptor: HttpInterceptorFn = (req, next) => {
  const supabaseService = inject(SupabaseService);

  // Get access token from Supabase service (for Supabase API calls)
  const token = supabaseService.getAccessToken();

  // Get FarmIQ ID from Supabase service signal
  const farmiqId = supabaseService.getFarmiqId();

  // Set up headers object
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Add Authorization header for Supabase calls
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Add X-FarmIQ-ID header for ALL API calls (critical for backend)
  if (farmiqId) {
    headers['X-FarmIQ-ID'] = farmiqId;
    console.log(`🔑 Added FarmIQ ID header: ${farmiqId}`);
  } else {
    console.warn('⚠️ No FarmIQ ID available in request headers');
  }

  // Add user role header if available (for backend routing optimization)
  const user = supabaseService.getUser();
  if (user?.user_metadata?.['role']) {
    headers['X-User-Role'] = user.user_metadata['role'];
  }

  // Clone request with headers
  req = req.clone({ setHeaders: headers });

  return next(req);
};
