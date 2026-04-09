import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { SupabaseService } from '../../../services/core/supabase.service';
import { RoleService } from '../services/role';

/**
 * Generic Role Guard
 * Checks if user has the required role specified in route data
 */
export const roleGuard: CanActivateFn = async (route, state) => {
  const supabaseService = inject(SupabaseService);
  const roleService = inject(RoleService);
  const router = inject(Router);

  const requiredRole = route.data['role'];
  
  if (!requiredRole) {
    console.warn('Role guard: No role specified in route data');
    return true;
  }

  try {
    const user = supabaseService.getUser();
    if (!user) {
      router.navigate(['/login']);
      return false;
    }

    const hasAccess = await roleService.checkRoleAccess(user.id, requiredRole);
    
    if (!hasAccess) {
      console.error(`Access denied: User does not have ${requiredRole} role`);
      router.navigate(['/unauthorized']);
      return false;
    }

    return true;
  } catch (error) {
    console.error('Role guard error:', error);
    router.navigate(['/login']);
    return false;
  }
};
