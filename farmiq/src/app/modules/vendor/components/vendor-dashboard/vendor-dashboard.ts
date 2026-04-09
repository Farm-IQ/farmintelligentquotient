import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { SupabaseService } from '../../../auth/services/supabase';

@Component({
  selector: 'app-vendor-dashboard',
  imports: [CommonModule],
  templateUrl: './vendor-dashboard.html',
  styleUrl: './vendor-dashboard.scss',
})
export class VendorDashboard {
  private supabaseService = inject(SupabaseService);
  private router = inject(Router);

  goToChatbot(): void {
     this.router.navigateByUrl('/farmgrow');
  }

  async signOut(): Promise<void> {
    try {
      console.log('🚪 Vendor signing out...');
      await this.supabaseService.signOut();
      console.log('✅ Vendor logged out successfully');
      // Navigate to login after logout
      this.router.navigate(['/login']);
    } catch (error) {
      console.error('❌ Logout error:', error);
      // Even if there's an error, navigate to login
      this.router.navigate(['/login']);
    }
  }
}
