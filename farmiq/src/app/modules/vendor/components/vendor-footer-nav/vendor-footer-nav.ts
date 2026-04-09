import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router, NavigationEnd } from '@angular/router';
import { IonIcon } from '@ionic/angular/standalone';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-vendor-footer-nav',
  standalone: true,
  imports: [CommonModule, RouterModule, IonIcon],
  templateUrl: './vendor-footer-nav.html',
  styleUrl: './vendor-footer-nav.scss'
})
export class VendorFooterNav implements OnInit {
  currentRoute = '';

  constructor(private router: Router) {}

  ngOnInit(): void {
    // Subscribe to route changes
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: any) => {
        this.currentRoute = event.url;
      });
  }

  isActive(route: string): boolean {
    return this.currentRoute.includes(route);
  }
}
