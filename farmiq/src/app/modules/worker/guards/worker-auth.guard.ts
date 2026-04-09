/**
 * Worker Auth Guard
 * Protects worker routes and ensures user is authenticated
 */

import { Injectable, inject } from '@angular/core';
import { Router, CanActivateFn, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { SupabaseService } from '../../auth/services/supabase';

@Injectable({
  providedIn: 'root'
})
export class WorkerAuthGuard {
  constructor(private supabase: SupabaseService, private router: Router) {}

  async canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Promise<boolean> {
    try {
      const client = await this.supabase.getSupabaseClient();
      const { data: { user } } = await client.auth.getUser();
      
      if (!user) {
        this.router.navigate(['/workers/login'], {
          queryParams: { returnUrl: state.url }
        });
        return false;
      }

      return true;
    } catch (err) {
      this.router.navigate(['/workers/login'], {
        queryParams: { returnUrl: state.url }
      });
      return false;
    }
  }
}

// Functional guard version (Angular 16+)
export const workerAuthGuard: CanActivateFn = async (route: ActivatedRouteSnapshot, state: RouterStateSnapshot) => {
  const supabase = inject(SupabaseService);
  const router = inject(Router);

  try {
    const client = await supabase.getSupabaseClient();
    const { data: { user } } = await client.auth.getUser();
    
    if (!user) {
      router.navigate(['/workers/login'], {
        queryParams: { returnUrl: state.url }
      });
      return false;
    }

    return true;
  } catch (err) {
    router.navigate(['/workers/login'], {
      queryParams: { returnUrl: state.url }
    });
    return false;
  }
};
