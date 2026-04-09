import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { IonIcon } from '@ionic/angular/standalone';
import { LenderService } from '../../services/lender';
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
  selector: 'app-lender-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule, FarmgrowChatbotComponent, IonIcon],
  templateUrl: './lender-navbar.html',
  styleUrl: './lender-navbar.scss'
})
export class LenderNavbar implements OnInit, OnDestroy {
  showNotifications = false;
  showProfile = false;
  showChatbot = false;
  notifications: Notification[] = [];
  unreadNotifications = 0;
  userName = 'Lender User';
  userEmail = 'lender@farmiq.com';
  userInitials = 'LU';
  private destroy$ = new Subject<void>();

  constructor(private lenderService: LenderService, private router: Router) {}

  ngOnInit(): void {
    this.loadUserProfile();
    this.loadNotifications();
    this.setupNotificationPolling();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadUserProfile(): void {
    this.lenderService.getUserProfile().pipe(takeUntil(this.destroy$)).subscribe({
      next: (profile: any) => {
        this.userName = `${profile.first_name} ${profile.last_name}`;
        this.userEmail = profile.email;
        this.userInitials = `${profile.first_name[0]}${profile.last_name[0]}`.toUpperCase();
      },
      error: (err: any) => console.error('Error loading profile:', err)
    });
  }

  private loadNotifications(): void {
    this.lenderService.getNotifications().pipe(takeUntil(this.destroy$)).subscribe({
      next: (notifs: any[]) => {
        this.notifications = notifs;
        this.unreadNotifications = notifs.filter((n: any) => !n.read).length;
      },
      error: (err: any) => console.error('Error loading notifications:', err)
    });
  }

  private setupNotificationPolling(): void {
    setInterval(() => this.loadNotifications(), 30000);
  }

  toggleNotifications(): void {
    this.showNotifications = !this.showNotifications;
    this.showProfile = false;
    if (this.showNotifications && this.unreadNotifications > 0) {
      this.lenderService.markNotificationsAsRead().pipe(takeUntil(this.destroy$)).subscribe();
    }
  }

  toggleProfile(): void {
    this.showProfile = !this.showProfile;
    this.showNotifications = false;
  }

  openChatbot(): void { this.showChatbot = true; }
  closeChatbot(): void { this.showChatbot = false; }

  getNotificationIcon(type: string): string {
    const iconMap: { [key: string]: string } = {
      'info': 'information-circle-outline',
      'warning': 'warning-outline',
      'success': 'checkmark-circle-outline',
      'error': 'alert-circle-outline'
    };
    return iconMap[type] || 'information-circle-outline';
  }

  logout(): void {
    this.lenderService.logout().subscribe({
      next: (res: any) => this.router.navigate(['/login'])
    });
  }
}
