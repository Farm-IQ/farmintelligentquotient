/**
 * Worker Footer Navigation Component
 * Bottom navigation for worker modules
 */

import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonIcon } from '@ionic/angular/standalone';
import { Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';

interface FooterLink {
  path: string;
  label: string;
  ionIcon: string;
}

@Component({
  selector: 'app-worker-footer-nav',
  standalone: true,
  imports: [CommonModule, IonIcon],
  templateUrl: './worker-footer-nav.html',
  styleUrls: ['./worker-footer-nav.scss']
})
export class WorkerFooterNavComponent implements OnInit {
  footerLinks: FooterLink[] = [
    { path: '/workers/dashboard', label: 'Dashboard', ionIcon: 'grid-outline' },
    { path: '/workers/attendance', label: 'Attendance', ionIcon: 'checkmark-circle-outline' },
    { path: '/workers/tasks', label: 'Tasks', ionIcon: 'list-outline' },
    { path: '/workers/payroll', label: 'Payroll', ionIcon: 'wallet-outline' },
    { path: '/workers/profile', label: 'Profile', ionIcon: 'person-outline' },
  ];

  activeRoute = '';
  private router = inject(Router);

  ngOnInit(): void {
    // Track route changes
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: any) => {
        this.activeRoute = event.urlAfterRedirects;
      });
  }

  isActive(path: string): boolean {
    return this.activeRoute.includes(path);
  }

  navigateTo(path: string): void {
    this.router.navigateByUrl(path);
  }
}
