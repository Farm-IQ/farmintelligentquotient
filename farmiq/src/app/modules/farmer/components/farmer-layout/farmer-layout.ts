import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FarmerNavbarComponent } from '../farmer-navbar/farmer-navbar';
import { FarmerFooterNavComponent } from '../farmer-footer-nav/farmer-footer-nav';

@Component({
  selector: 'app-farmer-layout',
  standalone: true,
  imports: [CommonModule, RouterModule, FarmerNavbarComponent, FarmerFooterNavComponent],
  templateUrl: './farmer-layout.html',
  styleUrl: './farmer-layout.scss'
})
export class FarmerLayoutComponent {}
