import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CooperativeService } from '../../services/cooperative';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-cooperative-bulk-credit-tool',
  imports: [CommonModule, FormsModule],
  templateUrl: './cooperative-bulk-credit-tool.html',
  styleUrl: './cooperative-bulk-credit-tool.scss',
})
export class CooperativeBulkCreditToolComponent implements OnInit, OnDestroy {
  private cooperativeService = inject(CooperativeService);
  private destroy$ = new Subject<void>();

  loading = false;
  running = false;
  error: string | null = null;
  successMessage: string | null = null;
  scoringProgress = 0;
  scoringResults: any = null;
  history: any[] = [];

  scoringConfig = {
    minFarmSize: 0.5,
    maxAge: 100,
    minimumScore: 0,
    includeNewMembers: true,
  };

  ngOnInit() {
    this.loadScoringHistory();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadScoringHistory() {
    this.loading = true;
    this.cooperativeService.getScoringHistory()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.history = data;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load scoring history';
          this.loading = false;
        }
      });
  }

  runBulkScoring() {
    this.running = true;
    this.error = null;
    this.successMessage = null;
    this.scoringProgress = 0;

    const simulateProgress = () => {
      if (this.scoringProgress < 100) {
        this.scoringProgress += Math.random() * 30;
        if (this.scoringProgress > 100) this.scoringProgress = 100;
        setTimeout(simulateProgress, 500);
      }
    };
    simulateProgress();

    this.cooperativeService.runBulkScoring()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (result) => {
          this.scoringResults = result;
          this.successMessage = `Scoring completed: ${result.membersScored} members scored`;
          this.running = false;
          this.scoringProgress = 100;
          this.loadScoringHistory();
        },
        error: (err) => {
          this.error = 'Failed to run bulk scoring';
          this.running = false;
        }
      });
  }

  getResultSummary(): string {
    if (!this.scoringResults) return '';
    return `${this.scoringResults.processedCount} members processed, ${this.scoringResults.successCount} successful`;
  }

  downloadReport() {
    if (!this.scoringResults) return;
    const data = JSON.stringify(this.scoringResults, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `scoring-report-${new Date().toISOString()}.json`;
    link.click();
  }
}
