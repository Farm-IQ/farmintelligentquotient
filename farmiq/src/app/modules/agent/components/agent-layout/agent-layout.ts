import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AgentNavbar } from '../agent-navbar/agent-navbar';
import { AgentFooterNav } from '../agent-footer-nav/agent-footer-nav';

@Component({
  selector: 'app-agent-layout',
  standalone: true,
  imports: [CommonModule, RouterModule, AgentNavbar, AgentFooterNav],
  templateUrl: './agent-layout.html',
  styleUrl: './agent-layout.scss'
})
export class AgentLayout {}
