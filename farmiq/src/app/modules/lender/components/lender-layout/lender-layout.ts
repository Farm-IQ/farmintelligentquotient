import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { LenderNavbar } from '../lender-navbar/lender-navbar';
import { LenderFooterNav } from '../lender-footer-nav/lender-footer-nav';

@Component({
  selector: 'app-lender-layout',
  standalone: true,
  imports: [CommonModule, RouterModule, LenderNavbar, LenderFooterNav],
  templateUrl: './lender-layout.html',
  styleUrl: './lender-layout.scss'
})
export class LenderLayout {}
