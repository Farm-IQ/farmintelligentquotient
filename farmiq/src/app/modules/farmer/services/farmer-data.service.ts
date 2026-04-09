/**
 * Farmer Data Service - Unified Service with Signals-based State Management
 * Handles all farmer profile and farm data without dual state (No BehaviorSubjects)
 */

import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError, of } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { FarmerProfile } from '../models/farmer-profile.models';
import { Farm, FarmParcel, FarmActivity } from '../models/livestock-operations.models';

export interface FarmData {
  id: string;
  farm_name: string;
  location: string;
  farm_size_acres: number;
  current_crop: string;
  planting_date: string;
  expected_harvest_date: string;
  soil_health: number; // 0-100
  water_availability: number; // 0-100
  estimated_yield: number;
  crop_stage: 'preparing' | 'planting' | 'growing' | 'harvesting' | 'post-harvest';
}

@Injectable({ providedIn: 'root' })
export class FarmerDataService {
  private apiUrl = environment.apiUrl;
  private supabaseUrl = `${environment.supabase.url}/rest/v1`;

  // ========== PRIMARY STATE (Signals Only) ==========
  farmerProfile = signal<FarmerProfile | null>(null);
  farmData = signal<FarmData | null>(null);
  farms = signal<Farm[]>([]);
  parcels = signal<FarmParcel[]>([]);
  activities = signal<FarmActivity[]>([]);
  loading = signal<boolean>(false);
  error = signal<string | null>(null);

  // ========== COMPUTED VALUES ==========
  hasFarm = computed(() => this.farmData() !== null);
  totalFarmSize = computed(() => {
    const farms = this.farms();
    return farms.reduce((sum, farm: Farm) => sum + (farm.size_acres || 0), 0);
  });
  
  daysToHarvest = computed(() => {
    const farm = this.farmData();
    if (!farm?.expected_harvest_date) return 0;
    const harvest = new Date(farm.expected_harvest_date);
    const today = new Date();
    return Math.ceil((harvest.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
  });

  cropStageProgress = computed(() => {
    const stage = this.farmData()?.crop_stage;
    const stages: Record<string, number> = {
      'preparing': 0,
      'planting': 25,
      'growing': 60,
      'harvesting': 90,
      'post-harvest': 100
    };
    return stages[stage || 'preparing'] || 0;
  });

  constructor(private http: HttpClient) {
    this.initializeFarmerData();
  }

  /**
   * Initialize farmer data on service creation
   */
  private initializeFarmerData(): void {
    const farmiqId = sessionStorage.getItem('farmiq_id');
    if (farmiqId) {
      this.getFarmerProfile(farmiqId).subscribe({
        next: (profiles) => {
          const profile = profiles && profiles.length > 0 ? profiles[0] : null;
          if (profile) {
            this.farmerProfile.set(profile);
            // Load farm data if profile exists
            if (profile.id) {
              this.getFarmData(profile.id).subscribe();
            }
          }
        },
        error: (err) => this.handleError('Failed to load farmer profile', err)
      });
    }
  }

  /**
   * Get farmer profile by FarmIQ ID
   */
  getFarmerProfile(farmiqId: string): Observable<FarmerProfile[]> {
    this.loading.set(true);
    return this.http.get<FarmerProfile[]>(
      `${this.supabaseUrl}/user_profiles?farmiq_id=eq.${farmiqId}`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((profiles: FarmerProfile[]) => {
        const profile = profiles[0] || null;
        this.farmerProfile.set(profile);
        this.loading.set(false);
      }),
      catchError((err) => {
        this.handleError('Failed to fetch farmer profile', err);
        return throwError(() => err);
      })
    );
  }

  /**
   * Get farm data for a farmer
   */
  getFarmData(farmerId: string): Observable<FarmData> {
    this.loading.set(true);
    return this.http.get<FarmData>(
      `${this.apiUrl}/farmers/${farmerId}/farm-data`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((data: FarmData) => {
        this.farmData.set(data);
        this.loading.set(false);
      }),
      catchError((err) => {
        this.handleError('Failed to fetch farm data', err);
        return throwError(() => err);
      })
    );
  }

  /**
   * Get all farms for a farmer
   */
  getFarms(farmerId: string): Observable<Farm[]> {
    this.loading.set(true);
    return this.http.get<Farm[]>(
      `${this.supabaseUrl}/farms?user_id=eq.${farmerId}`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((farmsData: Farm[]) => {
        this.farms.set(farmsData);
        this.loading.set(false);
      }),
      catchError((err) => {
        this.handleError('Failed to fetch farms', err);
        return throwError(() => err);
      })
    );
  }

  /**
   * Get parcels for a farm
   */
  getParcels(farmId: string): Observable<FarmParcel[]> {
    return this.http.get<FarmParcel[]>(
      `${this.supabaseUrl}/farm_parcels?farm_id=eq.${farmId}`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((parcelsData: FarmParcel[]) => {
        this.parcels.set(parcelsData);
      }),
      catchError((err) => {
        this.handleError('Failed to fetch parcels', err);
        return throwError(() => err);
      })
    );
  }

  /**
   * Get recent activities for farm
   */
  getActivities(farmId: string): Observable<FarmActivity[]> {
    return this.http.get<FarmActivity[]>(
      `${this.supabaseUrl}/farm_activities?farm_id=eq.${farmId}&order=created_at.desc&limit=10`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((activitiesData: FarmActivity[]) => {
        this.activities.set(activitiesData);
      }),
      catchError((err) => {
        this.handleError('Failed to fetch activities', err);
        return throwError(() => err);
      })
    );
  }

  /**
   * Update farm data (e.g., after soil sample, water check)
   */
  updateFarmData(farmId: string, updates: Partial<FarmData>): Observable<FarmData> {
    return this.http.patch<FarmData>(
      `${this.apiUrl}/farms/${farmId}`,
      updates,
      { headers: this.getHeaders() }
    ).pipe(
      tap((updatedData: FarmData) => {
        this.farmData.set(updatedData);
      }),
      catchError((err) => {
        this.handleError('Failed to update farm data', err);
        return throwError(() => err);
      })
    );
  }

  /**
   * Update crop stage (lifecycle tracking)
   */
  updateCropStage(farmId: string, stage: FarmData['crop_stage']): Observable<FarmData> {
    return this.updateFarmData(farmId, { crop_stage: stage });
  }

  /**
   * Refresh all farmer data
   */
  refreshData(): void {
    const profile = this.farmerProfile();
    if (profile?.id) {
      this.getFarmData(profile.id).subscribe();
      this.getFarms(profile.id).subscribe();
      this.getActivities(profile.id).subscribe();
    }
  }

  /**
   * Clear all state
   */
  clearData(): void {
    this.farmerProfile.set(null);
    this.farmData.set(null);
    this.farms.set([]);
    this.parcels.set([]);
    this.activities.set([]);
    this.error.set(null);
  }

  /**
   * Get HTTP headers with auth token
   */
  private getHeaders() {
    const farmiqId = sessionStorage.getItem('farmiq_id');
    const token = sessionStorage.getItem('auth_token');
    return {
      'Authorization': `Bearer ${token || ''}`,
      'apikey': environment.supabase.anonKey,
      'Content-Type': 'application/json',
      'X-FarmIQ-ID': farmiqId || ''
    };
  }

  /**
   * Handle service errors
   */
  private handleError(message: string, error: any): void {
    console.error(message, error);
    this.error.set(message);
    this.loading.set(false);
  }
}
