import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { FarmerService } from '../../services/farmer.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface CreditScore {
  score: number;
  rating: string;
  description: string;
  next_review_date: string;
  risk_factors: any[];
  loan_options: any[];
  improvement_tips: string[];
}

@Component({
  selector: 'app-farmer-credit-score',
  standalone: true,
  imports: [CommonModule, IonicModule],
  templateUrl: './farmer-credit-score.html',
  styleUrls: ['./farmer-credit-score.scss']
})
export class FarmerCreditScoreComponent implements OnInit, OnDestroy {
  creditScore: CreditScore | null = null;
  loading = true;
  error: string | null = null;
  private destroy$ = new Subject<void>();

  constructor(private farmerService: FarmerService) {}

  ngOnInit(): void {
    this.loadCreditScore();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadCreditScore(): void {
    this.loading = true;
    this.error = null;

    this.farmerService.getCreditScore()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (score: any) => {
          this.creditScore = score;
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load credit score';
          this.loading = false;
          console.error('Credit score load error:', err);
        }
      });
  }

  getScorePercentage(): number {
    return this.creditScore ? Math.min((this.creditScore.score / 100) * 100, 100) : 0;
  }
}
