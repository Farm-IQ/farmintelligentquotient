import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { IonIcon } from '@ionic/angular/standalone';
import { FarmerService } from '../../services/farmer.service';
import { FarmgrowChatbotComponent } from '../../../../components/farmgrow-chatbot/farmgrow-chatbot';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'success' | 'error';
  read: boolean;
  timestamp: Date;
}

@Component({
  selector: 'app-farmer-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule, FarmgrowChatbotComponent, IonIcon],
  templateUrl: './farmer-navbar.html',
  styleUrl: './farmer-navbar.scss'
})
export class FarmerNavbarComponent implements OnInit, OnDestroy {
  showNotifications = false;
  showProfile = false;
  showChatbot = false;
  
  notifications: Notification[] = [];
  unreadNotifications = 0;
  
  userName = 'John Farmer';
  userEmail = 'john@farm.com';
  userInitials = 'JF';
  
  private destroy$ = new Subject<void>();

  constructor(
    private farmerService: FarmerService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadUserProfile();
    this.loadNotifications();
    this.setupNotificationPolling();
  }

  private loadUserProfile(): void {
    this.farmerService.getUserProfile()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (profile) => {
          this.userName = `${profile.first_name} ${profile.last_name}`;
          this.userEmail = profile.email;
          this.userInitials = `${profile.first_name[0]}${profile.last_name[0]}`.toUpperCase();
        },
        error: (err) => console.error('Error loading profile:', err)
      });
  }

  private loadNotifications(): void {
    this.farmerService.getNotifications()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (notifs) => {
          this.notifications = notifs;
          this.unreadNotifications = notifs.filter(n => !n.read).length;
        },
        error: (err) => console.error('Error loading notifications:', err)
      });
  }

  private setupNotificationPolling(): void {
    // Poll for new notifications every 30 seconds
    setInterval(() => {
      this.loadNotifications();
    }, 30000);
  }

  toggleNotifications(): void {
    this.showNotifications = !this.showNotifications;
    this.showProfile = false;
    
    // Mark notifications as read when opened
    if (this.showNotifications && this.unreadNotifications > 0) {
      this.farmerService.markNotificationsAsRead()
        .pipe(takeUntil(this.destroy$))
        .subscribe();
    }
  }

  toggleProfile(): void {
    this.showProfile = !this.showProfile;
    this.showNotifications = false;
  }

  getNotificationIcon(type: string): string {
    const icons: Record<string, string> = {
      'info': 'information-circle-outline',
      'warning': 'warning-outline',
      'success': 'checkmark-circle-outline',
      'error': 'alert-circle-outline'
    };
    return icons[type] || 'notifications-outline';
  }

  openChatbot(): void {
    this.showChatbot = true;
  }

  closeChatbot(): void {
    this.showChatbot = false;
  }

  logout(): void {
    this.farmerService.logout().subscribe({
      next: () => {
        this.router.navigate(['/login']);
      },
      error: (err) => console.error('Logout error:', err)
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
