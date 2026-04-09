import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import {
  FarmerProfile,
  GpsCoordinate,
} from '../models/farmer-profile.models';
import {
  Farm,
  FarmParcel,
  FarmActivity,
  SoilSample,
  FarmerAssessment,
  FarmerStatistics
} from '../models/livestock-operations.models';

export interface FarmData {
  id?: string;
  farmName: string;
  location: string;
  size: number;
  cropType: string;
  season: string;
}

export interface CreditScore {
  userId: string;
  score: number;
  riskLevel: 'low' | 'medium' | 'high';
  lastUpdated: Date;
  eligibleAmount: number;
}

export interface ForexSignal {
  id: string;
  signal: 'buy' | 'sell' | 'hold' | 'strong_buy' | 'strong_sell';
  commodity: string;
  symbol?: string;
  predictedPrice: number;
  entry_price?: number;
  target_price?: number;
  stop_loss?: number;
  confidence: number;
  timestamp: Date;
}

export interface FarmerAnalytics {
  totalRevenue: number;
  yieldMetrics: Record<string, number>;
  soilHealth: number;
  weatherImpact: string;
  recommendations: string[];
}

@Injectable({
  providedIn: 'root',
})
export class FarmerService {
  private apiUrl = '/api/farmers';
  
  // Signals for reactive state
  farmDataSignal = signal<FarmData | null>(null);
  creditScoreSignal = signal<CreditScore | null>(null);
  analyticsSignal = signal<FarmerAnalytics | null>(null);
  farmerProfileSignal = signal<FarmerProfile | null>(null);
  farmsSignal = signal<Farm[]>([]);
  parcelsSignal = signal<FarmParcel[]>([]);
  activitiesSignal = signal<FarmActivity[]>([]);
  soilSamplesSignal = signal<SoilSample[]>([]);
  
  // BehaviorSubjects for backward compatibility
  private farmDataSubject = new BehaviorSubject<FarmData | null>(null);
  private creditScoreSubject = new BehaviorSubject<CreditScore | null>(null);
  private farmerProfileSubject = new BehaviorSubject<FarmerProfile | null>(null);
  private farmsSubject = new BehaviorSubject<Farm[]>([]);
  private parcelsSubject = new BehaviorSubject<FarmParcel[]>([]);
  
  farmData$ = this.farmDataSubject.asObservable();
  creditScore$ = this.creditScoreSubject.asObservable();
  farmerProfile$ = this.farmerProfileSubject.asObservable();
  farms$ = this.farmsSubject.asObservable();
  parcels$ = this.parcelsSubject.asObservable();

  constructor(private http: HttpClient) {
    this.initializeData();
  }

  /**
   * Initialize farmer data from backend
   */
  private initializeData(): void {
    this.getFarmData().subscribe(data => {
      this.farmDataSignal.set(data);
      this.farmDataSubject.next(data);
    });
  }

  /**
   * Get farmer's farm data
   */
  getFarmData(): Observable<FarmData> {
    return this.http.get<FarmData>(`${this.apiUrl}/farm-data`).pipe(
      tap(data => {
        this.farmDataSignal.set(data);
        this.farmDataSubject.next(data);
      })
    );
  }

  /**
   * Update farm data
   */
  updateFarmData(farmData: FarmData): Observable<FarmData> {
    return this.http.put<FarmData>(`${this.apiUrl}/farm-data`, farmData).pipe(
      tap(data => {
        this.farmDataSignal.set(data);
        this.farmDataSubject.next(data);
      })
    );
  }

  /**
   * Get FarmIQ credit score
   */
  getCreditScore(): Observable<CreditScore> {
    return this.http.get<CreditScore>(`${this.apiUrl}/credit-score`).pipe(
      tap(score => {
        this.creditScoreSignal.set(score);
        this.creditScoreSubject.next(score);
      })
    );
  }

  /**
   * Get forex/commodity signals
   */
  getForexSignals(): Observable<ForexSignal[]> {
    return this.http.get<ForexSignal[]>(`${this.apiUrl}/forex-signals`);
  }

  /**
   * Get AI agronomy recommendations (via chatbot)
   */
  getAgronomyRecommendations(query: string): Observable<{ recommendations: string[] }> {
    return this.http.post(`${this.apiUrl}/agronomy/chat`, { query }).pipe(
      map(response => response as { recommendations: string[] })
    );
  }

  /**
   * Get farm analytics
   */
  getAnalytics(): Observable<FarmerAnalytics> {
    return this.http.get<FarmerAnalytics>(`${this.apiUrl}/analytics`).pipe(
      tap(analytics => {
        this.analyticsSignal.set(analytics);
      })
    );
  }

  /**
   * Get wallet balance
   */
  getWalletBalance(): Observable<{ balance: number; currency: string }> {
    return this.http.get<{ balance: number; currency: string }>(`${this.apiUrl}/wallet/balance`);
  }

  /**
   * Transfer funds from wallet
   */
  transferFunds(amount: number, recipient: string): Observable<{ transactionId: string; status: string }> {
    return this.http.post<{ transactionId: string; status: string }>(`${this.apiUrl}/wallet/transfer`, { amount, recipient });
  }

  /**
   * Get farmer's transaction history
   */
  getTransactionHistory(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/wallet/transactions`);
  }

  /**
   * Update farmer settings
   */
  updateSettings(settings: Record<string, any>): Observable<Record<string, any>> {
    return this.http.put(`${this.apiUrl}/settings`, settings);
  }

  /**
   * Get farmer settings
   */
  getSettings(): Observable<Record<string, any>> {
    return this.http.get<Record<string, any>>(`${this.apiUrl}/settings`);
  }

  /**
   * Update farmer account/profile
   */
  updateProfile(profile: Record<string, any>): Observable<Record<string, any>> {
    return this.http.put(`${this.apiUrl}/profile`, profile);
  }

  /**
   * Get farmer profile
   */
  getProfile(): Observable<Record<string, any>> {
    return this.http.get<Record<string, any>>(`${this.apiUrl}/profile`);
  }

  // =========================================================================
  // GIS - FARM MANAGEMENT
  // =========================================================================

  /**
   * Get all farms for farmer
   */
  getFarms(): Observable<Farm[]> {
    return this.http.get<Farm[]>(`${this.apiUrl}/farms`).pipe(
      tap(farms => {
        this.farmsSignal.set(farms);
        this.farmsSubject.next(farms);
      })
    );
  }

  /**
   * Get single farm by ID
   */
  getFarm(farmId: string): Observable<Farm> {
    return this.http.get<Farm>(`${this.apiUrl}/farms/${farmId}`);
  }

  /**
   * Create new farm
   */
  createFarm(farmData: Partial<Farm>): Observable<Farm> {
    return this.http.post<Farm>(`${this.apiUrl}/farms`, farmData).pipe(
      tap(farm => {
        const farms = this.farmsSignal() || [];
        this.farmsSignal.set([...farms, farm]);
      })
    );
  }

  /**
   * Update farm
   */
  updateFarm(farmId: string, farmData: Partial<Farm>): Observable<Farm> {
    return this.http.put<Farm>(`${this.apiUrl}/farms/${farmId}`, farmData).pipe(
      tap(updated => {
        const farms = this.farmsSignal()?.map(f => f.id === farmId ? updated : f) || [];
        this.farmsSignal.set(farms);
      })
    );
  }

  /**
   * Delete farm
   */
  deleteFarm(farmId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/farms/${farmId}`).pipe(
      tap(() => {
        const farms = this.farmsSignal()?.filter(f => f.id !== farmId) || [];
        this.farmsSignal.set(farms);
      })
    );
  }

  // =========================================================================
  // GIS - PARCEL MANAGEMENT
  // =========================================================================

  /**
   * Get parcels for farm
   */
  getFarmParcels(farmId: string): Observable<FarmParcel[]> {
    return this.http.get<FarmParcel[]>(`${this.apiUrl}/farms/${farmId}/parcels`).pipe(
      tap(parcels => {
        this.parcelsSignal.set(parcels);
        this.parcelsSubject.next(parcels);
      })
    );
  }

  /**
   * Get single parcel
   */
  getParcel(parcelId: string): Observable<FarmParcel> {
    return this.http.get<FarmParcel>(`${this.apiUrl}/parcels/${parcelId}`);
  }

  /**
   * Create parcel in farm
   */
  createParcel(farmId: string, parcelData: Partial<FarmParcel>): Observable<FarmParcel> {
    return this.http.post<FarmParcel>(`${this.apiUrl}/farms/${farmId}/parcels`, parcelData).pipe(
      tap(parcel => {
        const parcels = this.parcelsSignal() || [];
        this.parcelsSignal.set([...parcels, parcel]);
      })
    );
  }

  /**
   * Update parcel
   */
  updateParcel(parcelId: string, parcelData: Partial<FarmParcel>): Observable<FarmParcel> {
    return this.http.put<FarmParcel>(`${this.apiUrl}/parcels/${parcelId}`, parcelData).pipe(
      tap(updated => {
        const parcels = this.parcelsSignal()?.map(p => p.id === parcelId ? updated : p) || [];
        this.parcelsSignal.set(parcels);
      })
    );
  }

  /**
   * Delete parcel
   */
  deleteParcel(parcelId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/parcels/${parcelId}`).pipe(
      tap(() => {
        const parcels = this.parcelsSignal()?.filter(p => p.id !== parcelId) || [];
        this.parcelsSignal.set(parcels);
      })
    );
  }

  // =========================================================================
  // GIS - ACTIVITY TRACKING
  // =========================================================================

  /**
   * Get activities for parcel
   */
  getParcelActivities(parcelId: string, startDate?: Date, endDate?: Date): Observable<FarmActivity[]> {
    let url = `${this.apiUrl}/parcels/${parcelId}/activities`;
    if (startDate && endDate) {
      url += `?startDate=${startDate.toISOString()}&endDate=${endDate.toISOString()}`;
    }
    return this.http.get<FarmActivity[]>(url);
  }

  /**
   * Log farm activity
   */
  logActivity(parcelId: string, activityData: Partial<FarmActivity>): Observable<FarmActivity> {
    return this.http.post<FarmActivity>(`${this.apiUrl}/parcels/${parcelId}/activities`, activityData);
  }

  /**
   * Update activity
   */
  updateActivity(activityId: string, activityData: Partial<FarmActivity>): Observable<FarmActivity> {
    return this.http.put<FarmActivity>(`${this.apiUrl}/activities/${activityId}`, activityData);
  }

  /**
   * Delete activity
   */
  deleteActivity(activityId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/activities/${activityId}`);
  }

  // =========================================================================
  // GIS - SOIL ANALYSIS
  // =========================================================================

  /**
   * Get soil samples for parcel
   */
  getParcelSoilSamples(parcelId: string): Observable<SoilSample[]> {
    return this.http.get<SoilSample[]>(`${this.apiUrl}/parcels/${parcelId}/soil-samples`).pipe(
      tap(samples => this.soilSamplesSignal.set(samples))
    );
  }

  /**
   * Record soil sample
   */
  recordSoilSample(parcelId: string, sampleData: Partial<SoilSample>): Observable<SoilSample> {
    return this.http.post<SoilSample>(`${this.apiUrl}/parcels/${parcelId}/soil-samples`, sampleData).pipe(
      tap(sample => {
        const samples = this.soilSamplesSignal() || [];
        this.soilSamplesSignal.set([...samples, sample]);
      })
    );
  }

  /**
   * Update soil sample
   */
  updateSoilSample(sampleId: string, sampleData: Partial<SoilSample>): Observable<SoilSample> {
    return this.http.put<SoilSample>(`${this.apiUrl}/soil-samples/${sampleId}`, sampleData);
  }

  /**
   * Get soil property map (kriged heatmap)
   */
  getSoilPropertyMap(parcelId: string, property: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/parcels/${parcelId}/soil-map?property=${property}`);
  }

  // =========================================================================
  // GIS - ASSESSMENTS
  // =========================================================================

  /**
   * Get farm assessment
   */
  getFarmAssessment(farmId: string): Observable<FarmerAssessment> {
    return this.http.get<FarmerAssessment>(`${this.apiUrl}/farms/${farmId}/assessment`);
  }

  /**
   * Request farm assessment
   */
  requestFarmAssessment(farmId: string): Observable<FarmerAssessment> {
    return this.http.post<FarmerAssessment>(`${this.apiUrl}/farms/${farmId}/assessment`, {});
  }

  /**
   * Get farmer statistics
   */
  getFarmerStatistics(): Observable<FarmerStatistics> {
    return this.http.get<FarmerStatistics>(`${this.apiUrl}/statistics`);
  }
}
