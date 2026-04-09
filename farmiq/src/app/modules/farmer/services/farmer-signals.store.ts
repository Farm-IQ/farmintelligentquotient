import { Injectable, signal, computed, effect } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';
import { Observable, Subject } from 'rxjs';

export interface TradingSignal {
  id: string;
  symbol: string;
  timeframe: string;
  direction: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  entryPrice: number;
  stopLoss: number;
  takeProfit: number;
  positionSize: number;
  backtested_accuracy: number;
  backtest_win_rate: number;
  model_version: string;
  generated_at: string;
  created_at: string;
}

export interface SignalGenerationJob {
  job_id: string;
  status: 'processing' | 'completed' | 'error';
  progress: number;
  signal?: TradingSignal;
  error_message?: string;
}

@Injectable({ providedIn: 'root' })
export class FarmerSignalsStore {
  // ========== Signals ==========
  signals = signal<TradingSignal[]>([]);
  isLoading = signal(false);
  selectedSymbol = signal<string>('EURUSD');
  currentUser = signal<string>('farmer-001');
  generationProgress = signal<number>(0);
  generationError = signal<string | null>(null);

  // ========== Computed Properties ==========
  latestSignal = computed(() => {
    const sigs = this.signals();
    return sigs.length > 0 ? sigs[0] : null;
  });

  filteredSignals = computed(() => {
    return this.signals().filter(
      s => s.symbol === this.selectedSymbol() && s.direction !== 'HOLD'
    );
  });

  buySignals = computed(() =>
    this.filteredSignals().filter(s => s.direction === 'BUY')
  );

  sellSignals = computed(() =>
    this.filteredSignals().filter(s => s.direction === 'SELL')
  );

  highConfidenceSignals = computed(() =>
    this.filteredSignals().filter(s => s.confidence > 0.7)
  );

  averageConfidence = computed(() => {
    const sigs = this.filteredSignals();
    if (sigs.length === 0) return 0;
    const sum = sigs.reduce((acc, s) => acc + s.confidence, 0);
    return sum / sigs.length;
  });

  totalWinRate = computed(() => {
    const sigs = this.filteredSignals();
    if (sigs.length === 0) return 0;
    const sum = sigs.reduce((acc, s) => acc + s.backtest_win_rate, 0);
    return sum / sigs.length;
  });

  private signalSubject = new Subject<TradingSignal>();
  signal$ = this.signalSubject.asObservable();

  constructor(private http: HttpClient) {
    // Load signals on initialization
    effect(() => {
      this.loadSignals();
    });

    // Auto-refresh every 30 seconds
    setInterval(() => {
      if (!this.isLoading()) {
        this.loadSignals();
      }
    }, 30000);
  }

  loadSignals() {
    this.isLoading.set(true);
    this.http.get<{ signals: TradingSignal[] }>(
      `${environment.backendUrl}api/farmsuite/signals/history?symbol=${this.selectedSymbol()}&limit=20`
    ).subscribe({
      next: (response) => {
        this.signals.set(response.signals || []);
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error('Load signals error:', err);
        this.isLoading.set(false);
      }
    });
  }

  generateSignal(symbol: string, timeframe: string = '15M') {
    this.isLoading.set(true);
    this.generationProgress.set(0);
    this.generationError.set(null);

    this.http.post<{ job_id: string }>(
      `${environment.backendUrl}api/farmsuite/signals/generate`,
      {
        user_id: this.currentUser(),
        symbol,
        timeframe,
        mode: 'live'
      }
    ).subscribe({
      next: (response) => {
        const jobId = response.job_id;
        this.pollJobStatus(jobId);
      },
      error: (err) => {
        const errorMsg = err.error?.detail || 'Failed to generate signal';
        this.generationError.set(errorMsg);
        this.isLoading.set(false);
        console.error('Generate signal error:', err);
      }
    });
  }

  private pollJobStatus(jobId: string) {
    const pollInterval = setInterval(() => {
      this.http.get<SignalGenerationJob>(
        `${environment.backendUrl}api/farmsuite/signals/status/${jobId}`
      ).subscribe({
        next: (job) => {
          this.generationProgress.set(job.progress);

          if (job.status === 'completed' && job.signal) {
            clearInterval(pollInterval);
            // Prepend new signal to list
            const current = this.signals();
            this.signals.set([job.signal, ...current]);
            this.signalSubject.next(job.signal);
            this.isLoading.set(false);
          } else if (job.status === 'error') {
            clearInterval(pollInterval);
            this.generationError.set(job.error_message || 'Signal generation failed');
            this.isLoading.set(false);
          }
        },
        error: (err) => {
          clearInterval(pollInterval);
          console.error('Poll job status error:', err);
          this.isLoading.set(false);
        }
      });
    }, 500); // Poll every 500ms
  }

  setSelectedSymbol(symbol: string) {
    this.selectedSymbol.set(symbol);
  }

  setCurrentUser(userId: string) {
    this.currentUser.set(userId);
  }
}
