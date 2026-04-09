import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { VendorNavbar } from '../vendor-navbar/vendor-navbar';
import { VendorFooterNav } from '../vendor-footer-nav/vendor-footer-nav';

@Component({
  selector: 'app-vendor-layout',
  standalone: true,
  imports: [CommonModule, RouterModule, VendorNavbar, VendorFooterNav],
  templateUrl: './vendor-layout.html',
  styleUrl: './vendor-layout.scss'
})
export class VendorLayout {}
