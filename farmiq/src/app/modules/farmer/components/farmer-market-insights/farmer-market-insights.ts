import { Component, OnInit, OnDestroy, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { FarmerService } from '../../services/farmer.service';

@Component({
  selector: 'app-farmer-market-insights',
  standalone: true,
  imports: [CommonModule, IonicModule],
  templateUrl: './farmer-market-insights.html',
  styleUrls: ['./farmer-market-insights.scss']
})
export class FarmerMarketInsightsComponent implements OnInit, OnDestroy {
  marketPrices = signal<any[]>([]);
  diseaseRisk = signal<any | null>(null);
  farmAnalysis = signal<any | null>(null);
  loading = signal<boolean>(true);
  error = signal<string | null>(null);

  private destroy$ = new Subject<void>();

  constructor(private farmerService: FarmerService) {}

  ngOnInit(): void {
    this.loading.set(true);
    
    // Load market prices
    this.farmerService.getMarketPrices()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (prices) => {
          this.marketPrices.set(prices);
          this.loading.set(false);
        },
        error: (err) => {
          this.error.set('Unable to load market prices');
          this.loading.set(false);
          console.error('Market prices error:', err);
        }
      });

    // Load disease risk
    this.farmerService.getDiseaseRisk()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (risk) => {
          this.diseaseRisk.set(risk);
        },
        error: (err) => {
          console.error('Disease risk error:', err);
        }
      });

    // Load farm analysis
    this.farmerService.getFarmAnalysis()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (analysis) => {
          this.farmAnalysis.set(analysis);
        },
        error: (err) => {
          console.error('Farm analysis error:', err);
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
