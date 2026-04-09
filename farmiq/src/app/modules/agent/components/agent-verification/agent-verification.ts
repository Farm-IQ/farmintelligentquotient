import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgentService } from '../../services/agent';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-agent-verification',
  imports: [CommonModule, FormsModule],
  templateUrl: './agent-verification.html',
  styleUrl: './agent-verification.scss',
})
export class AgentVerificationComponent implements OnInit, OnDestroy {
  private agentService = inject(AgentService);
  private destroy$ = new Subject<void>();

  pendingVerifications: any[] = [];
  currentVerification: any = null;
  loading = false;
  verifying = false;
  error: string | null = null;
  successMessage: string | null = null;

  verificationForm = {
    approved: false,
    comments: '',
    rejectionReason: '',
  };

  ngOnInit() {
    this.loadPendingVerifications();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadPendingVerifications() {
    this.loading = true;
    this.error = null;

    this.agentService.getPendingVerifications()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.pendingVerifications = data;
          if (this.pendingVerifications.length > 0) {
            this.selectVerification(this.pendingVerifications[0]);
          }
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load verifications';
          this.loading = false;
        }
      });
  }

  selectVerification(verification: any) {
    this.currentVerification = verification;
    this.verificationForm = {
      approved: false,
      comments: '',
      rejectionReason: '',
    };
  }

  submitVerification() {
    if (!this.currentVerification) return;

    if (!this.verificationForm.approved && !this.verificationForm.rejectionReason) {
      this.error = 'Please provide rejection reason';
      return;
    }

    this.verifying = true;
    this.error = null;
    this.successMessage = null;

    const verification: any = {
      farmerId: this.currentVerification.farmerId,
      farmerName: this.currentVerification.farmerName,
      idVerified: this.verificationForm.approved,
      addressVerified: false,
      phoneVerified: false,
      bankVerified: false,
      status: this.verificationForm.approved ? 'approved' : 'rejected',
      verificationDate: new Date(),
      verificationNotes: this.verificationForm.comments || this.verificationForm.rejectionReason,
    };

    this.agentService.submitVerification(verification)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.successMessage = `Verification submitted for ${this.currentVerification.farmerName}`;
          this.verifying = false;
          const index = this.pendingVerifications.indexOf(this.currentVerification);
          this.pendingVerifications.splice(index, 1);
          if (this.pendingVerifications.length > 0) {
            this.selectVerification(this.pendingVerifications[0]);
          } else {
            this.currentVerification = null;
          }
        },
        error: (err) => {
          this.error = 'Failed to submit verification';
          this.verifying = false;
        }
      });
  }

  skipVerification() {
    const index = this.pendingVerifications.indexOf(this.currentVerification);
    this.pendingVerifications.splice(index, 1);
    if (this.pendingVerifications.length > 0) {
      this.selectVerification(this.pendingVerifications[0]);
    }
  }

  getDocumentStatus(docType: string): string {
    const doc = this.currentVerification?.documents?.find((d: any) => d.type === docType);
    return doc?.status || 'pending';
  }
}
