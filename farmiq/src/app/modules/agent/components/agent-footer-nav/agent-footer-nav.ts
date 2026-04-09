import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router, NavigationEnd } from '@angular/router';
import { IonIcon } from '@ionic/angular/standalone';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-agent-footer-nav',
  standalone: true,
  imports: [CommonModule, RouterModule, IonIcon],
  templateUrl: './agent-footer-nav.html',
  styleUrl: './agent-footer-nav.scss'
})
export class AgentFooterNav implements OnInit {
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
