/**
 * Worker Module
 * Main module for worker-related functionality
 */

import { NgModule } from '@angular/core';
import { WorkerRoutingModule } from './worker-routing.module';
import { WorkerLayoutComponent } from './components/worker-layout/worker-layout';
import { WorkerNavbarComponent } from './components/worker-navbar/worker-navbar';
import { WorkerFooterNavComponent } from './components/worker-footer-nav/worker-footer-nav';

@NgModule({
  imports: [
    WorkerRoutingModule,
    WorkerLayoutComponent,
    WorkerNavbarComponent,
    WorkerFooterNavComponent,
  ],
  exports: [
    WorkerLayoutComponent,
    WorkerNavbarComponent,
    WorkerFooterNavComponent,
  ],
})
export class WorkerModule { }
