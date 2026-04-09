/**
 * Farmer Service - Integration with Supabase & AI Backend
 * Handles all farmer dashboard data, analytics, credit scoring, and trading signals
 */

import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError, of } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { SupabaseService } from '../../auth/services/supabase';
import { FarmerProfile, FarmerProfileUpdateRequest, GpsCoordinate } from '../models/farmer-profile.models';
import { Farm, FarmParcel, FarmActivity, SoilSample, FarmerAssessment, FarmerStatistics } from '../models/livestock-operations.models';

// Models
export interface FarmProfile {
  id: string;
  farmiq_id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  farm_name: string;
  farm_size_acres: number;
  location: string;
  crops: string[];
  created_at: string;
}

export interface FarmData {
  id: string;
  farm_size: number;
  location: string;
  soil_health: number;
  water_availability: number;
  current_crop: string;
  planting_date: string;
  expected_harvest: string;
  estimated_yield: number;
}

export interface AnalyticsData {
  yieldMetrics: {
    current_season: number;
    last_season: number;
    average: number;
  };
  weatherImpact: number;
  soilHealth: number;
  waterUsage: number;
  recommendations: string[];
}

export interface CreditScore {
  score: number;
  riskLevel: 'low' | 'medium' | 'high';
  factors: Array<{
    name: string;
    value: number;
    impact: string;
  }>;
  updated_at: string;
}

export interface WalletData {
  balance: number;
  currency: string;
  transactions: Transaction[];
}

export interface Transaction {
  id: string;
  type: 'credit' | 'debit';
  amount: number;
  description: string;
  date: string;
  status: 'completed' | 'pending' | 'failed';
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'success' | 'error';
  read: boolean;
  timestamp: Date;
}

export interface FarmerAnalytics {
  totalArea: number;
  yieldPerHectare: number;
  revenue: number;
}

@Injectable({
  providedIn: 'root'
})
export class FarmerService {
  private apiUrl = 'http://localhost:8000/api/v1';
  private supabaseUrl = `${environment.supabase.url}/rest/v1`;
  private supabaseAnonKey = environment.supabase.anonKey;
  private loading$ = new BehaviorSubject<boolean>(false);
  private error$ = new BehaviorSubject<string | null>(null);

  constructor(private http: HttpClient, private supabase: SupabaseService) {
    this.initializeSession();
  }

  private initializeSession(): void {
    // Check if user is already logged in
    const farmiqId = sessionStorage.getItem('farmiq_id');
    if (!farmiqId) {
      // For demo: use a test ID if not set
      const testId = 'test-farmer-001';
      sessionStorage.setItem('farmiq_id', testId);
      console.log('Session initialized with test ID:', testId);
    }
  }

  // =========================================================================
  // USER PROFILE
  // =========================================================================

  getUserProfile(): Observable<FarmProfile> {
    const farmiqId = sessionStorage.getItem('farmiq_id');
    const headers = this.getHeaders();

    return this.http.get<FarmProfile>(
      `${this.supabaseUrl}/user_profiles?farmiq_id=eq.${farmiqId}`,
      { headers }
    ).pipe(
      tap(profile => console.log('Profile loaded:', profile)),
      catchError(err => this.handleError('Error loading profile', err))
    );
  }

  updateUserProfile(profile: Partial<FarmProfile>): Observable<FarmProfile> {
    const farmiqId = sessionStorage.getItem('farmiq_id');
    const headers = this.getHeaders();

    return this.http.patch<FarmProfile>(
      `${this.supabaseUrl}/user_profiles?farmiq_id=eq.${farmiqId}`,
      profile,
      { headers }
    ).pipe(
      tap(() => console.log('Profile updated')),
      catchError(err => this.handleError('Error updating profile', err))
    );
  }

  /**
   * Get current farm for authenticated user
   * Returns Observable for compatibility with components
   */
  getCurrentFarm(): Observable<Farm | null> {
    return new Observable(observer => {
      this.getCurrentFarmAsync()
        .then(farm => {
          observer.next(farm);
          observer.complete();
        })
        .catch(err => {
          observer.error(err);
        });
    });
  }

  /**
   * Async version: Get current farm for authenticated user
   */
  private async getCurrentFarmAsync(): Promise<Farm | null> {
    try {
      const client = await this.supabase.getSupabaseClient();
      const { data: { user } } = await client.auth.getUser();

      if (!user?.id) {
        console.warn('No authenticated user');
        return null;
      }

      const { data: farm, error } = await client
        .from('farms')
        .select('*')
        .eq('user_id', user.id)
        .single();

      if (error) {
        console.warn('No farm found for user');
        return null;
      }

      return farm as Farm || null;
    } catch (err) {
      console.error('Error loading current farm:', err);
      return null;
    }
  }

  // =========================================================================
  // FARM DATA
  // =========================================================================

  getFarmData(): Observable<FarmData> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.get<any>(
      `${this.supabaseUrl}/farms?user_id=eq.${farmiqId}`,
      { headers }
    ).pipe(
      tap(farms => {
        console.log('Farm data loaded:', farms);
        if (!farms || farms.length === 0) {
          console.warn('No farm data found for user');
        }
      }),
      catchError(err => {
        console.error('Error loading farm data:', err);
        // Return mock data for demo purposes
        return new Observable<FarmData>(observer => {
          observer.next({
            id: 'farm-001',
            farm_size: 5,
            location: 'Kiambu County',
            soil_health: 75,
            water_availability: 65,
            current_crop: 'Maize',
            planting_date: '2025-12-15',
            expected_harvest: '2026-04-15',
            estimated_yield: 1200
          } as FarmData);
          observer.complete();
        });
      })
    );
  }

  updateFarmData(data: FarmData): Observable<FarmData> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.patch<FarmData>(
      `${this.supabaseUrl}/farms?farmiq_id=eq.${farmiqId}`,
      data,
      { headers }
    ).pipe(
      tap(() => console.log('Farm data updated')),
      catchError(err => {
        console.error('Error updating farm data:', err);
        return new Observable<FarmData>(observer => {
          observer.next(data);
          observer.complete();
        });
      })
    );
  }

  // =========================================================================
  // ANALYTICS
  // =========================================================================

  getAnalytics(): Observable<AnalyticsData> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.get<any>(
      `${this.supabaseUrl}/farm_analytics?farmiq_id=eq.${farmiqId}`,
      { headers }
    ).pipe(
      tap(data => console.log('Analytics loaded:', data)),
      catchError(err => {
        console.error('Error loading analytics:', err);
        // Return mock data for demo purposes
        return new Observable<AnalyticsData>(observer => {
          observer.next({
            yieldMetrics: {
              current_season: 1200,
              last_season: 950,
              average: 1050
            },
            weatherImpact: 75,
            soilHealth: 78,
            waterUsage: 65,
            recommendations: [
              'Increase irrigation frequency due to low rainfall',
              'Apply nitrogen fertilizer in next 2 weeks',
              'Monitor for armyworm pest activity'
            ]
          });
          observer.complete();
        });
      })
    );
  }

  // =========================================================================
  // CREDIT SCORING (FarmIQ AI)
  // =========================================================================

  getCreditScore(): Observable<CreditScore> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.get<CreditScore>(
      `${this.apiUrl}/farmiq/score/${farmiqId}`,
      { headers }
    ).pipe(
      tap(score => console.log('Credit score loaded:', score)),
      catchError(err => {
        console.error('Error loading credit score:', err);
        // Return mock credit score for demo
        return new Observable<CreditScore>(observer => {
          observer.next({
            score: 65,
            riskLevel: 'medium',
            factors: [
              { name: 'Farm Size', value: 5, impact: 'positive' },
              { name: 'Years Experience', value: 8, impact: 'positive' }
            ],
            updated_at: new Date().toISOString()
          });
          observer.complete();
        });
      })
    );
  }

  requestCreditScoring(): Observable<CreditScore> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    const payload = {
      farmiq_id: farmiqId,
      farm_size: 100,
      annual_income: 50000,
      debt_history: 'clean'
    };

    return this.http.post<CreditScore>(
      `${this.apiUrl}/farmiq/score`,
      payload,
      { headers }
    ).pipe(
      tap(score => console.log('Credit score calculated:', score)),
      catchError(err => {
        console.error('Error calculating credit score:', err);
        return new Observable<CreditScore>(observer => {
          observer.next({
            score: 65,
            riskLevel: 'medium',
            factors: [
              { name: 'Farm Size', value: 5, impact: 'positive' },
              { name: 'Years Experience', value: 8, impact: 'positive' }
            ],
            updated_at: new Date().toISOString()
          });
          observer.complete();
        });
      })
    );
  }

  // =========================================================================
  // FarmSuite - Farm Intelligence & Predictions
  // =========================================================================

  /**
   * Get farm analysis with predictions (yield, disease risk, market prices)
   */
  getFarmAnalysis(): Observable<any> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.get<any>(
      `${this.apiUrl}/farmsuite/farm-analysis/${farmiqId}`,
      { headers }
    ).pipe(
      tap(analysis => console.log('Farm analysis loaded:', analysis)),
      catchError(err => {
        console.error('Error loading farm analysis:', err);
        // Return mock farm analysis
        return of({
          farmiq_id: farmiqId,
          yield_prediction: { current: 1200, forecast: 1350, unit: 'kg' },
          disease_risk: { risk_level: 'low', diseases: ['blight'], confidence: 0.75 },
          market_prices: [
            { commodity: 'maize', price: 42.5, change: 2.5, trend: 'up' },
            { commodity: 'coffee', price: 195.3, change: -5.2, trend: 'down' }
          ],
          weather_impact: { moisture: 65, temperature: 25, optimal: true }
        });
      })
    );
  }

  /**
   * Get market prices for commodities
   */
  getMarketPrices(): Observable<any[]> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.get<any[]>(
      `${this.apiUrl}/farmsuite/market-prices`,
      { headers }
    ).pipe(
      tap(prices => console.log('Market prices loaded:', prices)),
      catchError(err => {
        console.error('Error loading market prices:', err);
        return of([
          { commodity: 'maize', price: 42.5, change: 2.5, trend: 'up' },
          { commodity: 'coffee', price: 195.3, change: -5.2, trend: 'down' },
          { commodity: 'beans', price: 85.0, change: 0, trend: 'neutral' }
        ]);
      })
    );
  }

  /**
   * Get disease risk assessment for farm
   */
  getDiseaseRisk(): Observable<any> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.get<any>(
      `${this.apiUrl}/farmsuite/disease-risk/${farmiqId}`,
      { headers }
    ).pipe(
      tap(risk => console.log('Disease risk loaded:', risk)),
      catchError(err => {
        console.error('Error loading disease risk:', err);
        return of({
          risk_level: 'medium',
          diseases: [
            { name: 'maize blight', probability: 0.45, season: 'long_rains' },
            { name: 'coffee leaf rust', probability: 0.65, season: 'short_rains' }
          ]
        });
      })
    );
  }

  // =========================================================================
  // FarmScore - Credit Scoring & Risk Assessment
  // =========================================================================

  /**
   * Get credit score for farmer
   */
  getFarmScore(): Observable<CreditScore> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.get<CreditScore>(
      `${this.apiUrl}/farmscore/score/${farmiqId}`,
      { headers }
    ).pipe(
      tap(score => console.log('FarmScore loaded:', score)),
      catchError(err => {
        console.error('Error loading FarmScore:', err);
        // Return mock credit score
        return of({
          score: 72,
          riskLevel: 'medium',
          factors: [
            { name: 'Payment History', value: 85, impact: 'positive' },
            { name: 'Farm Size', value: 60, impact: 'neutral' },
            { name: 'Crop Diversity', value: 70, impact: 'positive' },
            { name: 'Debt Ratio', value: 45, impact: 'negative' }
          ],
          updated_at: new Date().toISOString()
        } as CreditScore);
      })
    );
  }

  /**
   * Get score history and trends
   */
  getFarmScoreHistory(): Observable<any[]> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.get<any[]>(
      `${this.apiUrl}/farmscore/history/${farmiqId}`,
      { headers }
    ).pipe(
      tap(history => console.log('FarmScore history loaded:', history)),
      catchError(err => {
        console.error('Error loading FarmScore history:', err);
        return of([
          { date: '2025-12-01', score: 68, riskLevel: 'medium' },
          { date: '2026-01-01', score: 70, riskLevel: 'medium' },
          { date: '2026-02-01', score: 71, riskLevel: 'medium' },
          { date: '2026-03-01', score: 72, riskLevel: 'medium' }
        ]);
      })
    );
  }

  // =========================================================================
  // WALLET & TRANSACTIONS
  // =========================================================================

  getWalletBalance(): Observable<WalletData> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.get<any>(
      `${this.supabaseUrl}/wallets?farmiq_id=eq.${farmiqId}`,
      { headers }
    ).pipe(
      tap(wallet => console.log('Wallet loaded:', wallet)),
      catchError(err => {
        console.error('Error loading wallet:', err);
        // Return mock wallet for demo
        return new Observable<WalletData>(observer => {
          observer.next({
            balance: 125000,
            currency: 'KES',
            transactions: [
              { id: '1', type: 'credit', amount: 50000, date: '2026-02-05', description: 'Loan disbursement', status: 'completed' },
              { id: '2', type: 'debit', amount: 5000, date: '2026-02-03', description: 'Loan payment', status: 'completed' }
            ]
          });
          observer.complete();
        });
      })
    );
  }

  getTransactionHistory(): Observable<Transaction[]> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.get<Transaction[]>(
      `${this.supabaseUrl}/loan_payments?farmiq_id=eq.${farmiqId}&order=payment_date.desc`,
      { headers }
    ).pipe(
      tap(transactions => console.log('Transactions loaded:', transactions)),
      catchError(err => {
        console.error('Error loading transactions:', err);
        // Return mock transactions for demo
        return new Observable<Transaction[]>(observer => {
          observer.next([
            { id: '1', type: 'credit', amount: 50000, date: '2026-02-05', description: 'Loan disbursement' } as any,
            { id: '2', type: 'debit', amount: 5000, date: '2026-02-03', description: 'Loan payment' } as any,
            { id: '3', type: 'credit', amount: 15000, date: '2026-02-01', description: 'Input subsidy' } as any
          ]);
          observer.complete();
        });
      })
    );
  }

  // =========================================================================
  // NOTIFICATIONS
  // =========================================================================

  getNotifications(): Observable<Notification[]> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.get<Notification[]>(
      `${this.supabaseUrl}/notifications?farmiq_id=eq.${farmiqId}&is_read=eq.false`,
      { headers }
    ).pipe(
      tap(notifications => console.log('Notifications loaded:', notifications)),
      catchError(err => {
        console.error('Error loading notifications:', err);
        // Return mock notifications for demo
        return new Observable<Notification[]>(observer => {
          observer.next([
            { id: '1', title: 'Loan due', message: 'Your loan payment is due on 2026-02-15', date: '2026-02-05' } as any,
            { id: '2', title: 'Weather alert', message: 'Light rains expected this weekend', date: '2026-02-04' } as any,
            { id: '3', title: 'Price update', message: 'Maize prices increased by 5%', date: '2026-02-03' } as any
          ]);
          observer.complete();
        });
      })
    );
  }

  markNotificationsAsRead(): Observable<void> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.patch<void>(
      `${this.supabaseUrl}/notifications?farmiq_id=eq.${farmiqId}`,
      { is_read: true },
      { headers }
    ).pipe(
      tap(() => console.log('Notifications marked as read')),
      catchError(err => {
        console.error('Error marking notifications as read:', err);
        return new Observable<void>(observer => {
          observer.next();
          observer.complete();
        });
      })
    );
  }

  // =========================================================================
  // AUTHENTICATION
  // =========================================================================

  logout(): Observable<void> {
    sessionStorage.removeItem('farmiq_id');
    sessionStorage.removeItem('user_id');
    sessionStorage.removeItem('auth_token');

    return new Observable(observer => {
      observer.next();
      observer.complete();
    });
  }

  // =========================================================================
  // HELPER METHODS
  // =========================================================================

  private getHeaders(): HttpHeaders {
    const token = sessionStorage.getItem('auth_token');
    const farmiqId = sessionStorage.getItem('farmiq_id');

    let headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'apikey': this.supabaseAnonKey
    });

    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }

    if (farmiqId) {
      headers = headers.set('X-FarmIQ-ID', farmiqId);
    }

    return headers;
  }

  private handleError(message: string, error: any) {
    console.error(message, error);
    this.error$.next(message);
    return throwError(() => new Error(message));
  }

  // Observable getters
  get loading(): Observable<boolean> {
    return this.loading$.asObservable();
  }

  get error(): Observable<string | null> {
    return this.error$.asObservable();
  }

  // =========================================================================
  // SETTINGS METHODS
  // =========================================================================

  getSettings(): Observable<any> {
    const farmiqId = sessionStorage.getItem('farmiq_id');
    const headers = this.getHeaders();

    return this.http.get<any>(
      `${this.supabaseUrl}/user_profiles?farmiq_id=eq.${farmiqId}`,
      { headers }
    ).pipe(
      catchError(err => this.handleError('Error loading settings', err))
    );
  }

  updateSettings(settings: any): Observable<any> {
    const farmiqId = sessionStorage.getItem('farmiq_id');
    const headers = this.getHeaders();

    return this.http.patch<any>(
      `${this.supabaseUrl}/user_profiles?farmiq_id=eq.${farmiqId}`,
      settings,
      { headers }
    ).pipe(
      catchError(err => this.handleError('Error updating settings', err))
    );
  }

  // =========================================================================
  // PROFILE METHODS
  // =========================================================================

  getProfile(): Observable<any> {
    return this.getUserProfile();
  }

  updateProfile(profile: any): Observable<any> {
    return this.updateUserProfile(profile);
  }

  // =========================================================================
  // WALLET METHODS
  // =========================================================================

  transferFunds(amount: number, recipient: string): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}/wallet/transfer`,
      { amount, recipient_id: recipient },
      { headers: this.getHeaders() }
    ).pipe(
      catchError(err => this.handleError('Error transferring funds', err))
    );
  }

  // =========================================================================
  // GIS - FARMER PROFILE MANAGEMENT
  // =========================================================================

  /**
   * Get farmer profile (GIS integrated)
   */
  getFarmerProfile(): Observable<FarmerProfile> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.get<FarmerProfile>(
      `${this.supabaseUrl}/farmer_profiles?farmiq_id=eq.${farmiqId}`,
      { headers }
    ).pipe(
      tap(profile => console.log('Farmer profile loaded:', profile)),
      catchError(err => this.handleError('Error loading farmer profile', err))
    );
  }

  /**
   * Update farmer profile (GIS integrated)
   */
  updateFarmerProfile(profile: FarmerProfileUpdateRequest): Observable<FarmerProfile> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.patch<FarmerProfile>(
      `${this.supabaseUrl}/farmer_profiles?farmiq_id=eq.${farmiqId}`,
      profile,
      { headers }
    ).pipe(
      tap(() => console.log('Farmer profile updated')),
      catchError(err => this.handleError('Error updating farmer profile', err))
    );
  }

  // =========================================================================
  // GIS - FARM MANAGEMENT
  // =========================================================================

  /**
   * Get all farms for current farmer
   */
  getFarms(): Observable<Farm[]> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.get<Farm[]>(
      `${this.supabaseUrl}/farms?user_id=eq.${farmiqId}`,
      { headers }
    ).pipe(
      tap(farms => console.log('Farms loaded:', farms)),
      catchError(err => this.handleError('Error loading farms', err))
    );
  }

  /**
   * Get single farm by ID
   */
  getFarm(farmId: string): Observable<Farm> {
    const headers = this.getHeaders();
    return this.http.get<Farm>(
      `${this.supabaseUrl}/farms?id=eq.${farmId}`,
      { headers }
    ).pipe(
      catchError(err => this.handleError('Error loading farm', err))
    );
  }

  /**
   * Create new farm
   */
  createFarm(farmData: Partial<Farm>): Observable<Farm> {
    const headers = this.getHeaders();
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';

    return this.http.post<Farm>(
      `${this.supabaseUrl}/farms`,
      { ...farmData, user_id: farmiqId },
      { headers }
    ).pipe(
      tap(farm => console.log('Farm created:', farm)),
      catchError(err => this.handleError('Error creating farm', err))
    );
  }

  /**
   * Update farm
   */
  updateFarm(farmId: string, farmData: Partial<Farm>): Observable<Farm> {
    const headers = this.getHeaders();

    return this.http.patch<Farm>(
      `${this.supabaseUrl}/farms?id=eq.${farmId}`,
      farmData,
      { headers }
    ).pipe(
      tap(() => console.log('Farm updated')),
      catchError(err => this.handleError('Error updating farm', err))
    );
  }

  /**
   * Delete farm
   */
  deleteFarm(farmId: string): Observable<void> {
    const headers = this.getHeaders();

    return this.http.delete<void>(
      `${this.supabaseUrl}/farms?id=eq.${farmId}`,
      { headers }
    ).pipe(
      tap(() => console.log('Farm deleted')),
      catchError(err => this.handleError('Error deleting farm', err))
    );
  }

  // =========================================================================
  // GIS - PARCEL MANAGEMENT
  // =========================================================================

  /**
   * Get all parcels for a farm
   */
  getFarmParcels(farmId: string): Observable<FarmParcel[]> {
    const headers = this.getHeaders();

    return this.http.get<FarmParcel[]>(
      `${this.supabaseUrl}/farm_parcels?farm_id=eq.${farmId}`,
      { headers }
    ).pipe(
      tap(parcels => console.log('Parcels loaded:', parcels)),
      catchError(err => this.handleError('Error loading parcels', err))
    );
  }

  /**
   * Get single parcel by ID
   */
  getParcel(parcelId: string): Observable<FarmParcel> {
    const headers = this.getHeaders();

    return this.http.get<FarmParcel>(
      `${this.supabaseUrl}/farm_parcels?id=eq.${parcelId}`,
      { headers }
    ).pipe(
      catchError(err => this.handleError('Error loading parcel', err))
    );
  }

  /**
   * Create parcel in a farm
   */
  createParcel(farmId: string, parcelData: Partial<FarmParcel>): Observable<FarmParcel> {
    const headers = this.getHeaders();

    return this.http.post<FarmParcel>(
      `${this.supabaseUrl}/farm_parcels`,
      { ...parcelData, farm_id: farmId },
      { headers }
    ).pipe(
      tap(parcel => console.log('Parcel created:', parcel)),
      catchError(err => this.handleError('Error creating parcel', err))
    );
  }

  /**
   * Update parcel
   */
  updateParcel(parcelId: string, parcelData: Partial<FarmParcel>): Observable<FarmParcel> {
    const headers = this.getHeaders();

    return this.http.patch<FarmParcel>(
      `${this.supabaseUrl}/farm_parcels?id=eq.${parcelId}`,
      parcelData,
      { headers }
    ).pipe(
      tap(() => console.log('Parcel updated')),
      catchError(err => this.handleError('Error updating parcel', err))
    );
  }

  /**
   * Delete parcel
   */
  deleteParcel(parcelId: string): Observable<void> {
    const headers = this.getHeaders();

    return this.http.delete<void>(
      `${this.supabaseUrl}/farm_parcels?id=eq.${parcelId}`,
      { headers }
    ).pipe(
      tap(() => console.log('Parcel deleted')),
      catchError(err => this.handleError('Error deleting parcel', err))
    );
  }

  // =========================================================================
  // GIS - ACTIVITY TRACKING
  // =========================================================================

  /**
   * Get activities for parcel with optional date filtering
   */
  getParcelActivities(parcelId: string, startDate?: Date, endDate?: Date): Observable<FarmActivity[]> {
    const headers = this.getHeaders();
    let url = `${this.supabaseUrl}/farm_activities?parcel_id=eq.${parcelId}`;

    if (startDate) {
      url += `&activity_date=gte.${startDate.toISOString()}`;
    }
    if (endDate) {
      url += `&activity_date=lte.${endDate.toISOString()}`;
    }

    return this.http.get<FarmActivity[]>(url, { headers }).pipe(
      tap(activities => console.log('Activities loaded:', activities)),
      catchError(err => this.handleError('Error loading activities', err))
    );
  }

  /**
   * Log farm activity (planting, spraying, irrigation, etc.)
   */
  logActivity(parcelId: string, activityData: Partial<FarmActivity>): Observable<FarmActivity> {
    const headers = this.getHeaders();

    return this.http.post<FarmActivity>(
      `${this.supabaseUrl}/farm_activities`,
      { ...activityData, parcel_id: parcelId },
      { headers }
    ).pipe(
      tap(activity => console.log('Activity logged:', activity)),
      catchError(err => this.handleError('Error logging activity', err))
    );
  }

  /**
   * Update activity
   */
  updateActivity(activityId: string, activityData: Partial<FarmActivity>): Observable<FarmActivity> {
    const headers = this.getHeaders();

    return this.http.patch<FarmActivity>(
      `${this.supabaseUrl}/farm_activities?id=eq.${activityId}`,
      activityData,
      { headers }
    ).pipe(
      tap(() => console.log('Activity updated')),
      catchError(err => this.handleError('Error updating activity', err))
    );
  }

  /**
   * Delete activity
   */
  deleteActivity(activityId: string): Observable<void> {
    const headers = this.getHeaders();

    return this.http.delete<void>(
      `${this.supabaseUrl}/farm_activities?id=eq.${activityId}`,
      { headers }
    ).pipe(
      tap(() => console.log('Activity deleted')),
      catchError(err => this.handleError('Error deleting activity', err))
    );
  }

  // =========================================================================
  // GIS - SOIL ANALYSIS
  // =========================================================================

  /**
   * Get soil samples for parcel
   */
  getParcelSoilSamples(parcelId: string): Observable<SoilSample[]> {
    const headers = this.getHeaders();

    return this.http.get<SoilSample[]>(
      `${this.supabaseUrl}/soil_samples?parcel_id=eq.${parcelId}`,
      { headers }
    ).pipe(
      tap(samples => console.log('Soil samples loaded:', samples)),
      catchError(err => this.handleError('Error loading soil samples', err))
    );
  }

  /**
   * Record soil sample with analysis data
   */
  recordSoilSample(parcelId: string, sampleData: Partial<SoilSample>): Observable<SoilSample> {
    const headers = this.getHeaders();

    return this.http.post<SoilSample>(
      `${this.supabaseUrl}/soil_samples`,
      { ...sampleData, parcel_id: parcelId },
      { headers }
    ).pipe(
      tap(sample => console.log('Soil sample recorded:', sample)),
      catchError(err => this.handleError('Error recording soil sample', err))
    );
  }

  /**
   * Update soil sample
   */
  updateSoilSample(sampleId: string, sampleData: Partial<SoilSample>): Observable<SoilSample> {
    const headers = this.getHeaders();

    return this.http.patch<SoilSample>(
      `${this.supabaseUrl}/soil_samples?id=eq.${sampleId}`,
      sampleData,
      { headers }
    ).pipe(
      tap(() => console.log('Soil sample updated')),
      catchError(err => this.handleError('Error updating soil sample', err))
    );
  }

  /**
   * Get soil property map (kriged heatmap for soil properties)
   */
  getSoilPropertyMap(parcelId: string, property: string): Observable<any> {
    const headers = this.getHeaders();

    return this.http.get<any>(
      `${this.supabaseUrl}/soil_maps?parcel_id=eq.${parcelId}&property=eq.${property}`,
      { headers }
    ).pipe(
      catchError(err => this.handleError('Error loading soil property map', err))
    );
  }

  // =========================================================================
  // GIS - ASSESSMENTS & STATISTICS
  // =========================================================================

  /**
   * Get latest farm assessment
   */
  getFarmAssessment(farmId: string): Observable<FarmerAssessment> {
    const headers = this.getHeaders();

    return this.http.get<FarmerAssessment>(
      `${this.supabaseUrl}/farmer_assessments?farm_id=eq.${farmId}&order=assessment_date.desc&limit=1`,
      { headers }
    ).pipe(
      tap(assessment => console.log('Farm assessment loaded:', assessment)),
      catchError(err => this.handleError('Error loading farm assessment', err))
    );
  }

  /**
   * Request new farm assessment
   */
  requestFarmAssessment(farmId: string): Observable<FarmerAssessment> {
    const headers = this.getHeaders();
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';

    return this.http.post<FarmerAssessment>(
      `${this.supabaseUrl}/farmer_assessments`,
      { 
        farm_id: farmId, 
        farmer_id: farmiqId, 
        assessment_date: new Date().toISOString(),
        assessment_type: 'automated'
      },
      { headers }
    ).pipe(
      tap(() => console.log('Assessment requested')),
      catchError(err => this.handleError('Error requesting assessment', err))
    );
  }

  /**
   * Get farmer statistics and aggregated metrics
   */
  getFarmerStatistics(): Observable<FarmerStatistics> {
    const farmiqId = sessionStorage.getItem('farmiq_id') || 'test-farmer-001';
    const headers = this.getHeaders();

    return this.http.get<FarmerStatistics>(
      `${this.supabaseUrl}/farmer_statistics?farmer_id=eq.${farmiqId}`,
      { headers }
    ).pipe(
      tap(stats => console.log('Farmer statistics loaded:', stats)),
      catchError(err => this.handleError('Error loading farmer statistics', err))
    );
  }

  // =========================================================================
  // LIVESTOCK & AGRIBUSINESS OPERATIONS
  // =========================================================================

  /**
   * Get overview of farm operations (crops, livestock, financial)
   */
  getFarmOperationsOverview(farmId: string): Observable<any> {
    const headers = this.getHeaders();

    return this.http.get(
      `${this.supabaseUrl}/farm_operations?farm_id=eq.${farmId}`,
      { headers }
    ).pipe(
      tap(operations => console.log(`✅ Loaded farm operations for farm ${farmId}`)),
      catchError(err => this.handleError('Error loading farm operations', err))
    );
  }

  /**
   * Get financial summary for a farm
   */
  getFarmFinancialSummary(farmId: string, startDate?: string, endDate?: string): Observable<any> {
    const headers = this.getHeaders();
    let url = `${this.supabaseUrl}/farm_financial_summary?farm_id=eq.${farmId}`;
    if (startDate) url += `&period_start=gte.${startDate}`;
    if (endDate) url += `&period_end=lte.${endDate}`;

    return this.http.get(
      url,
      { headers }
    ).pipe(
      tap(summary => console.log(`📊 Financial summary loaded for farm ${farmId}`)),
      catchError(err => this.handleError('Error loading financial summary', err))
    );
  }

  /**
   * Get livestock operations for a farm
   */
  getFarmLivestock(farmId: string): Observable<any[]> {
    const headers = this.getHeaders();

    return this.http.get<any[]>(
      `${this.supabaseUrl}/farm_livestock_units?farm_id=eq.${farmId}`,
      { headers }
    ).pipe(
      tap(livestock => console.log(`🐄 Loaded ${livestock.length} livestock units`)),
      catchError(err => this.handleError('Error loading livestock', err))
    );
  }

  /**
   * Get inventory for a farm
   */
  getFarmInventory(farmId: string): Observable<any[]> {
    const headers = this.getHeaders();

    return this.http.get<any[]>(
      `${this.supabaseUrl}/farm_inventory?farm_id=eq.${farmId}`,
      { headers }
    ).pipe(
      tap(inventory => console.log(`📦 Loaded ${inventory.length} inventory items`)),
      catchError(err => this.handleError('Error loading inventory', err))
    );
  }

  /**
   * Record livestock production metrics
   */
  recordProductionMetrics(livestockUnitId: string, metrics: any): Observable<any> {
    const headers = this.getHeaders();

    return this.http.post(
      `${this.supabaseUrl}/livestock_production_records`,
      { livestock_unit_id: livestockUnitId, ...metrics },
      { headers }
    ).pipe(
      tap(() => console.log('✅ Production metrics recorded')),
      catchError(err => this.handleError('Error recording production metrics', err))
    );
  }

  /**
   * Record farm cost
   */
  recordFarmCost(farmId: string, cost: any): Observable<any> {
    const headers = this.getHeaders();

    return this.http.post(
      `${this.supabaseUrl}/farm_costs`,
      { farm_id: farmId, ...cost },
      { headers }
    ).pipe(
      tap(() => console.log('💰 Farm cost recorded')),
      catchError(err => this.handleError('Error recording farm cost', err))
    );
  }

  /**
   * Record farm revenue
   */
  recordFarmRevenue(farmId: string, revenue: any): Observable<any> {
    const headers = this.getHeaders();

    return this.http.post(
      `${this.supabaseUrl}/farm_revenue`,
      { farm_id: farmId, ...revenue },
      { headers }
    ).pipe(
      tap(() => console.log('💵 Farm revenue recorded')),
      catchError(err => this.handleError('Error recording farm revenue', err))
    );
  }

  /**
   * Get coffee operations for a farm
   */
  getCoffeeOperations(farmId: string): Observable<any[]> {
    const headers = this.getHeaders();

    return this.http.get<any[]>(
      `${this.supabaseUrl}/coffee_operations?farm_id=eq.${farmId}`,
      { headers }
    ).pipe(
      tap(operations => console.log(`☕ Loaded ${operations.length} coffee operations`)),
      catchError(err => this.handleError('Error loading coffee operations', err))
    );
  }

  /**
   * Get dairy operations for a farm
   */
  getDairyOperations(farmId: string): Observable<any[]> {
    const headers = this.getHeaders();

    return this.http.get<any[]>(
      `${this.supabaseUrl}/dairy_operations?farm_id=eq.${farmId}`,
      { headers }
    ).pipe(
      tap(operations => console.log(`🥛 Loaded ${operations.length} dairy operations`)),
      catchError(err => this.handleError('Error loading dairy operations', err))
    );
  }
}
