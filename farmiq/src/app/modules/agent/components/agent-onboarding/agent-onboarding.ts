import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AgentService } from '../../services/agent';
import { SupabaseService } from '../../../auth/services/supabase';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-agent-onboarding',
  imports: [CommonModule, FormsModule],
  templateUrl: './agent-onboarding.html',
  styles: [`
    .agent-onboarding {
      .onboarding-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 1px solid #e5e7eb;
      }

      .onboarding-header h1 {
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        color: #1f2937;
      }

      .onboarding-header .header-actions {
        display: flex;
        gap: 12px;
        align-items: center;
      }

      .btn-chat,
      .btn-signout {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 16px;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        white-space: nowrap;
      }

      .btn-chat {
        background-color: #3b82f6;
        color: white;
      }

      .btn-chat:hover {
        background-color: #2563eb;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
      }

      .btn-chat:active {
        transform: translateY(0);
      }

      .btn-signout {
        background-color: #e5e7eb;
        color: #1f2937;
      }

      .btn-signout:hover {
        background-color: #d1d5db;
        transform: translateY(-2px);
      }

      .btn-signout:active {
        transform: translateY(0);
      }

      .chat-icon,
      .signout-icon {
        font-size: 16px;
      }

      .btn-text {
        display: inline;
      }

      @media (max-width: 640px) {
        .onboarding-header {
          flex-direction: column;
          align-items: flex-start;
          gap: 12px;
        }

        .btn-chat .btn-text,
        .btn-signout .btn-text {
          display: none;
        }
      }
    }
  `],
})
export class AgentOnboardingComponent implements OnInit, OnDestroy {
  private agentService = inject(AgentService);
  private supabaseService = inject(SupabaseService);
  private router = inject(Router);
  private destroy$ = new Subject<void>();

  onboardingList: any[] = [];
  loading = false;
  error: string | null = null;
  successMessage: string | null = null;
  showNewForm = false;
  activeTab = 'pending';

  newFarmer: any = {
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    location: '',
    farmSize: 0,
    cropType: '',
    idNumber: '',
    status: 'pending' as const,
  };

  ngOnInit() {
    this.loadOnboardingData();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadOnboardingData() {
    this.loading = true;
    this.error = null;

    this.agentService.getOnboardingList()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.onboardingList = data;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load onboarding data';
          this.loading = false;
        }
      });
  }

  getFilteredList(): any[] {
    if (this.activeTab === 'pending') {
      return this.onboardingList.filter(item => item.status === 'pending');
    }
    return this.onboardingList.filter(item => item.status === 'completed');
  }

  submitNewFarmer() {
    if (!this.newFarmer.firstName || !this.newFarmer.email) {
      this.error = 'First name and email are required';
      return;
    }

    this.agentService.onboardFarmer(this.newFarmer)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.successMessage = `${this.newFarmer.firstName} onboarded successfully`;
          this.showNewForm = false;
          this.newFarmer = { firstName: '', lastName: '', email: '', phone: '', location: '', farmSize: 0, cropType: '', idNumber: '', status: 'pending' };
          this.loadOnboardingData();
        },
        error: (err) => {
          this.error = 'Failed to onboard farmer';
        }
      });
  }

  updateStatus(onboardingId: string, newStatus: 'pending' | 'verified' | 'rejected') {
    this.agentService.updateOnboardingStatus(onboardingId, newStatus)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.loadOnboardingData();
        },
        error: (err) => {
          this.error = 'Failed to update status';
        }
      });
  }

  getStatusColor(status: string): string {
    const colors: { [key: string]: string } = {
      'pending': '#FFC107',
      'completed': '#4CAF50',
      'failed': '#F44336',
    };
    return colors[status.toLowerCase()] || '#999';
  }

  goToChatbot(): void {
    this.router.navigateByUrl('/farmgrow');
  }

  async signOut(): Promise<void> {
    try {
      console.log('🚪 Agent signing out...');
      await this.supabaseService.signOut();
      console.log('✅ Agent logged out successfully');
      // Navigate to login after logout
      this.router.navigate(['/login']);
    } catch (error) {
      console.error('❌ Logout error:', error);
      // Even if there's an error, navigate to login
      this.router.navigate(['/login']);
    }
  }
}
