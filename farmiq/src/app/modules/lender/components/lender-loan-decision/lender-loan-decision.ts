import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LenderService } from '../../services/lender';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-lender-loan-decision',
  imports: [CommonModule, FormsModule],
  templateUrl: './lender-loan-decision.html',
  styleUrl: './lender-loan-decision.scss',
})
export class LenderLoanDecisionComponent implements OnInit, OnDestroy {
  private lenderService = inject(LenderService);
  private destroy$ = new Subject<void>();

  applications: any[] = [];
  currentApplication: any = null;
  loading = false;
  deciding = false;
  error: string | null = null;
  successMessage: string | null = null;

  decisionForm = {
    approved: false,
    loanAmount: 0,
    interestRate: 0,
    tenure: 12,
    conditions: '',
  };

  ngOnInit() {
    this.loadPendingApplications();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadPendingApplications() {
    this.loading = true;
    this.error = null;

    this.lenderService.getPendingApplications()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.applications = data;
          if (this.applications.length > 0) {
            this.selectApplication(this.applications[0]);
          }
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load applications';
          this.loading = false;
        }
      });
  }

  selectApplication(app: any) {
    this.currentApplication = app;
    this.decisionForm = {
      approved: false,
      loanAmount: app.requestedAmount || 0,
      interestRate: 8.5,
      tenure: 12,
      conditions: '',
    };
  }

  submitDecision() {
    if (!this.currentApplication) return;

    this.deciding = true;
    this.error = null;
    this.successMessage = null;

    const decision: any = {
      loanId: this.currentApplication.id,
      decision: this.decisionForm.approved ? ('approve' as const) : ('reject' as const),
      reason: this.decisionForm.conditions,
      approvedAmount: this.decisionForm.loanAmount,
      approvedInterestRate: this.decisionForm.interestRate,
      conditions: [],
    };

    this.lenderService.makeLoanDecision(decision)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.successMessage = `Decision submitted for ${this.currentApplication.farmerName}`;
          this.deciding = false;
          const index = this.applications.indexOf(this.currentApplication);
          this.applications.splice(index, 1);
          if (this.applications.length > 0) {
            this.selectApplication(this.applications[0]);
          } else {
            this.currentApplication = null;
          }
        },
        error: (err) => {
          this.error = 'Failed to submit decision';
          this.deciding = false;
        }
      });
  }

  skipApplication() {
    const index = this.applications.indexOf(this.currentApplication);
    this.applications.splice(index, 1);
    if (this.applications.length > 0) {
      this.selectApplication(this.applications[0]);
    }
  }

  calculateMonthlyPayment(): number {
    const monthlyRate = this.decisionForm.interestRate / 100 / 12;
    const numPayments = this.decisionForm.tenure;
    if (monthlyRate === 0) return this.decisionForm.loanAmount / numPayments;
    return (
      (this.decisionForm.loanAmount * monthlyRate * Math.pow(1 + monthlyRate, numPayments)) /
      (Math.pow(1 + monthlyRate, numPayments) - 1)
    );
  }
}
