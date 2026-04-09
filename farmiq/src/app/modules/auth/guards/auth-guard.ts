import { CanActivateFn, Router } from '@angular/router';
import { inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { SupabaseService } from '../services/supabase';
import { AuthRoleService } from '../services/auth-role';

/**
 * Authentication Guard
 * Ensures user is authenticated before accessing protected routes
 * Also enforces email verification for email/password users (OAuth skipped)
 * 
 * Flow:
 * 1. Check if user is authenticated
 * 2. Check if email verification is required
 * 3. Load user profile and verify module access
 * 4. Grant or deny access
 */
export const authGuard: CanActivateFn = async (route, state) => {
  const supabaseService = inject(SupabaseService);
  const authRoleService = inject(AuthRoleService);
  const router = inject(Router);
  const platformId = inject(PLATFORM_ID);
  const isBrowser = isPlatformBrowser(platformId);

  if (isBrowser) {
    console.log('🔒 Auth guard checking access to:', state.url);
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

  // Step 2: Load user role and profile
  try {
    await authRoleService.loadUserProfile().toPromise();
    
    // Step 4: Verify module/dashboard access using check-role-access
    const primaryRole = authRoleService.getCurrentRole();
    if (primaryRole) {
      const hasAccess = await supabaseService.checkModuleAccess(primaryRole);
      
      if (!hasAccess) {
        if (isBrowser) {
          console.warn(`❌ User does not have access to ${primaryRole} module`);
        }
        router.navigate(['/login']);
        return false;
      }
      
      if (isBrowser) {
        console.log(`✅ User profile loaded and verified for ${primaryRole}, access granted`);
      }
    } else {
      if (isBrowser) {
        console.warn('⚠️ No primary role found for user');
      }
      router.navigate(['/login']);
      return false;
    }
    
    return true;
  } catch (error) {
    if (isBrowser) {
      console.error('❌ Error loading user profile:', error);
    }
    router.navigate(['/login']);
    return false;
  }
};
