import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { CooperativeNavbar } from '../cooperative-navbar/cooperative-navbar';
import { CooperativeFooterNav } from '../cooperative-footer-nav/cooperative-footer-nav';

@Component({
  selector: 'app-cooperative-layout',
  standalone: true,
  imports: [CommonModule, RouterModule, CooperativeNavbar, CooperativeFooterNav],
  templateUrl: './cooperative-layout.html',
  styleUrl: './cooperative-layout.scss'
})
export class CooperativeLayout {}
