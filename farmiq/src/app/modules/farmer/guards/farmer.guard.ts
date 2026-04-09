import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { SupabaseService } from '../../../modules/auth/services/supabase';
import { RoleService } from '../../../modules/auth/services/role';
import type { UserRoleType } from '../../../modules/auth/models';

/**
 * Farmer Role Guard
 * Ensures user has Farmer role
 * Protects farmer-specific routes and features
 */
export const farmerGuard: CanActivateFn = async (route, state) => {
  const supabaseService = inject(SupabaseService);
  const roleService = inject(RoleService);
  const router = inject(Router);

  try {
    const user = supabaseService.getUser();
    if (!user) {
      router.navigate(['/login']);
      return false;
    }

    const hasAccess = await roleService.checkRoleAccess(user.id, 'farmer' as UserRoleType);
    if (!hasAccess) {
      router.navigate(['/unauthorized']);
      return false;
    }
    return true;
  } catch (error) {
    console.error('Farmer guard error:', error);
    router.navigate(['/login']);
    return false;
  }
};
