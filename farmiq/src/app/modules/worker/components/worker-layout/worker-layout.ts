/**
 * Worker Layout Component
 * Main layout wrapper for all worker modules with navbar and footer
 */

import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { WorkerNavbarComponent } from '../worker-navbar/worker-navbar';
import { WorkerFooterNavComponent } from '../worker-footer-nav/worker-footer-nav';

@Component({
  selector: 'app-worker-layout',
  standalone: true,
  imports: [CommonModule, RouterModule, WorkerNavbarComponent, WorkerFooterNavComponent],
  templateUrl: './worker-layout.html',
  styleUrls: ['./worker-layout.scss']
})
export class WorkerLayoutComponent {}
