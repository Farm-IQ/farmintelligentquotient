/**
 * Worker Navbar Component
 * Shared navbar for all worker modules with role-based features
 */

import { Component, OnInit, OnDestroy, Optional } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { IonIcon } from '@ionic/angular/standalone';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'success' | 'error';
  read: boolean;
  timestamp: Date;
}

@Component({
  selector: 'app-worker-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule, IonIcon],
  templateUrl: './worker-navbar.html',
  styleUrls: ['./worker-navbar.scss']
})
export class WorkerNavbarComponent implements OnInit, OnDestroy {
  showNotifications = false;
  showProfile = false;
  showChatbot = false;

  notifications: Notification[] = [];
  unreadNotifications = 0;

  workerName = 'Farm Worker';
  userInitials = 'FW';

  private destroy$ = new Subject<void>();

  constructor(private router: Router) {}

  ngOnInit(): void {
    this.loadWorkerProfile();
    this.loadNotifications();
    this.setupNotificationPolling();
  }

  private loadWorkerProfile(): void {
    // Load worker profile - simplified pending service updates
    this.workerName = 'Farm Worker';
    this.userInitials = 'FW';
  }

  private loadNotifications(): void {
    // Load notifications from service
    // this.workerService.getNotifications()
    //   .pipe(takeUntil(this.destroy$))
    //   .subscribe(notifs => {
    //     this.notifications = notifs;
    //     this.unreadNotifications = notifs.filter(n => !n.read).length;
    //   });
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
      // this.workerService.markNotificationsAsRead()
      //   .pipe(takeUntil(this.destroy$))
      //   .subscribe();
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
    // Logout logic - navigate to login
    this.router.navigate(['/login']);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
