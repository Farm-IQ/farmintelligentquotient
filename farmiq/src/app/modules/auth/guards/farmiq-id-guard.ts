import { CanActivateFn, Router } from '@angular/router';
import { inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { SupabaseService } from '../services/supabase';
import { AuthRoleService } from '../services/auth-role';

/**
 * FarmIQ ID Guard
 * Ensures user has a valid FarmIQ ID before accessing FarmGrow Chatbot
 * FarmIQ ID is only granted after successful signup
 * 
 * Flow:
 * 1. User must be authenticated (has valid session)
 * 2. User must have completed signup (has FarmIQ ID)
 * 3. User can access FarmGrow Chatbot
 */
export const farmiqIdGuard: CanActivateFn = async (route, state) => {
  const supabaseService = inject(SupabaseService);
  const authRoleService = inject(AuthRoleService);
  const router = inject(Router);
  const platformId = inject(PLATFORM_ID);
  const isBrowser = isPlatformBrowser(platformId);

  if (isBrowser) {
    console.log('🔐 FarmIQ ID Guard - Checking access to:', state.url);
  }

  // Step 1: Check if user is authenticated
  if (!supabaseService.isAuthenticated()) {
    if (isBrowser) {
      console.log('❌ User not authenticated, redirecting to login');
    }
    router.navigate(['/login'], { queryParams: { returnUrl: state.url } });
    return false;
  }

  if (isBrowser) {
    console.log('✅ User authenticated');
  }

  // Step 2: Load user profile to check for FarmIQ ID
  try {
    const userProfile = await authRoleService.loadUserProfile().toPromise();
    if (isBrowser) {
      console.log('✅ User profile loaded');
    }

    // Step 3: Check if user has a valid FarmIQ ID
    if (!userProfile?.farmiq_id || userProfile.farmiq_id.trim() === '') {
      if (isBrowser) {
        console.log('❌ User does not have a FarmIQ ID - signup not completed');
      }
      // Redirect to signup to complete profile
      router.navigate(['/signup'], { 
        queryParams: { 
          returnUrl: state.url,
          reason: 'FarmIQ ID required to access chatbot'
        } 
      });
      return false;
    }

    if (isBrowser) {
      console.log(`✅ User has valid FarmIQ ID: ${userProfile.farmiq_id}`);
    }
    return true;

  } catch (error) {
    console.error('❌ Error loading user profile:', error);
    router.navigate(['/login']);
    return false;
  }
};
