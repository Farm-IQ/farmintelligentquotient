/**
 * Comprehensive Farmer Dashboard Service
 * Connects to Supabase for real-time farm and worker data
 * Replaces separate stub services with unified data layer
 * 
 * Features:
 * - Real farmer profile data
 * - Farm management (list, create, update)
 * - Crop tracking
 * - Worker management
 * - Real-time subscriptions
 * - Credit score integration
 * 
 * Architecture:
 * - Direct Supabase queries (no edge functions)
 * - Signal-based reactivity
 * - Error handling and retry logic
 * - Progress indicators
 */

import { Injectable, inject, signal, computed } from '@angular/core';
import { SupabaseService } from '../../auth/services/supabase';
import { SupabaseClient } from '@supabase/supabase-js';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';

// ============================================================================
// FARMER PROFILE MODELS
// ============================================================================

export interface FarmProfile {
  id: string;
  user_id: string;
  farm_name: string;
  county: string;
  location: string;
  latitude: number;
  longitude: number;
  size_acres: number;
  primary_crop: string;
  farming_method: 'rainfed' | 'irrigated' | 'mixed';
  years_farming: number;
  soil_type: string;
  created_at: string;
  updated_at: string;
}

export interface Farm {
  id: string;
  user_id: string;
  name: string;
  county: string;
  location: string;
  latitude: number;
  longitude: number;
  size_acres: number;
  soil_type: string;
  created_at: string;
  updated_at: string;
}

export interface Crop {
  id: string;
  farm_id: string;
  name: string;
  crop_type: string;
  variety: string;
  planting_date: string;
  expected_harvest_date: string;
  area_planted_acres: number;
  status: 'active' | 'harvested' | 'failed';
  health_status: string;
  created_at: string;
  updated_at: string;
}

export interface WorkerProfile {
  id: string;
  user_id: string;
  farm_id: string;
  worker_type: 'seasonal' | 'permanent' | 'casual' | 'contract';
  skills: string;
  certifications: string;
  years_experience: number;
  employment_status: 'active' | 'inactive' | 'on_leave' | 'terminated';
  employment_start_date: string;
  employment_end_date: string;
  county: string;
  location: string;
  metadata: any;
  created_at: string;
  updated_at: string;
}

export interface DashboardAnalyticsData {
  totalFarms: number;
  totalCrops: number;
  activeCrops: number;
  totalWorkers: number;
  activeWorkers: number;
  totalFarmSize: number;
  lastUpdated: string;
}

export interface CreditScore {
  score: number;
  grade: string;
  recommendation: string;
  factors: {
    farming_history: number;
    loan_repayment: number;
    farm_productivity: number;
    assets: number;
  };
  updatedAt: string;
}

// ============================================================================
// FARMER DASHBOARD SERVICE
// ============================================================================

@Injectable({
  providedIn: 'root'
})
export class FarmerDashboardService {
  private supabase = inject(SupabaseService);
  private http = inject(HttpClient);
  private supabaseClient: SupabaseClient | null = null;
  private readonly apiUrl = environment.apiUrl || 'http://localhost:8000';

  // ========================================================================
  // STATE SIGNALS
  // ========================================================================

  // Farmer Profile
  farmerProfile = signal<FarmProfile | null>(null);
  
  // Farms
  farms = signal<Farm[]>([]);
  selectedFarm = signal<Farm | null>(null);
  
  // Crops
  crops = signal<Crop[]>([]);
  activeCrops = computed(() => this.crops().filter(c => c.status === 'active'));
  
  // Workers
  workers = signal<WorkerProfile[]>([]);
  activeWorkers = computed(() => this.workers().filter(w => w.employment_status === 'active'));
  
  // Analytics
  analytics = signal<DashboardAnalyticsData | null>(null);
  creditScore = signal<CreditScore | null>(null);
  
  // Loading States
  isLoading = signal<boolean>(false);
  error = signal<string | null>(null);

  // ========================================================================
  // COMPUTED VALUES
  // ========================================================================

  totalFarmSize = computed(() =>
    this.farms().reduce((total, farm) => total + (farm.size_acres || 0), 0)
  );

  farmCount = computed(() => this.farms().length);

  workerCount = computed(() => this.workers().length);

  healthStatus = computed(() => {
    const actCrops = this.activeCrops();
    if (actCrops.length === 0) return 'No active crops';
    
    const healthy = actCrops.filter(c => c.health_status === 'good').length;
    const percentage = Math.round((healthy / actCrops.length) * 100);
    return `${percentage}% crops healthy`;
  });

  constructor() {
    this.initializeSupabaseClient();
  }

  // ========================================================================
  // INITIALIZATION
  // ========================================================================

  private async initializeSupabaseClient(): Promise<void> {
    try {
      this.supabaseClient = await this.supabase.getSupabaseClient();
    } catch (error) {
      console.error('❌ Failed to initialize Supabase client:', error);
      this.error.set('Failed to initialize database connection');
    }
  }

  // ========================================================================
  // FARMER PROFILE METHODS
  // ========================================================================

  /**
   * Load farmer profile from user_profiles + farmer_profiles
   */
  async loadFarmerProfile(userId: string): Promise<FarmProfile | null> {
    try {
      this.isLoading.set(true);
      this.error.set(null);

      if (!this.supabaseClient) await this.initializeSupabaseClient();

      const { data, error } = await this.supabaseClient!
        .from('farmer_profiles')
        .select('*')
        .eq('user_id', userId)
        .single();

      if (error) throw error;

      this.farmerProfile.set(data);
      console.log('✅ Farmer profile loaded:', data);
      return data;
    } catch (error: any) {
      console.error('❌ Error loading farmer profile:', error);
      this.error.set(error.message || 'Failed to load farmer profile');
      return null;
    } finally {
      this.isLoading.set(false);
    }
  }

  /**
   * Update farmer profile
   */
  async updateFarmerProfile(userId: string, updates: Partial<FarmProfile>): Promise<boolean> {
    try {
      this.isLoading.set(true);
      this.error.set(null);

      if (!this.supabaseClient) await this.initializeSupabaseClient();

      const { error } = await this.supabaseClient!
        .from('farmer_profiles')
        .update(updates)
        .eq('user_id', userId);

      if (error) throw error;

      // Reload profile
      await this.loadFarmerProfile(userId);
      console.log('✅ Farmer profile updated');
      return true;
    } catch (error: any) {
      console.error('❌ Error updating farmer profile:', error);
      this.error.set(error.message || 'Failed to update profile');
      return false;
    } finally {
      this.isLoading.set(false);
    }
  }

  // ========================================================================
  // FARMS METHODS
  // ========================================================================

  /**
   * Load all farms for a user
   */
  async loadFarms(userId: string): Promise<Farm[]> {
    try {
      this.isLoading.set(true);
      this.error.set(null);

      if (!this.supabaseClient) await this.initializeSupabaseClient();

      const { data, error } = await this.supabaseClient!
        .from('farms')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false });

      if (error) throw error;

      this.farms.set(data || []);
      
      // Auto-select first farm if available
      if (data && data.length > 0) {
        this.selectedFarm.set(data[0]);
      }

      console.log(`✅ Loaded ${data?.length || 0} farms`);
      return data || [];
    } catch (error: any) {
      console.error('❌ Error loading farms:', error);
      this.error.set(error.message || 'Failed to load farms');
      return [];
    } finally {
      this.isLoading.set(false);
    }
  }

  /**
   * Create a new farm
   */
  async createFarm(userId: string, farmData: Partial<Farm>): Promise<Farm | null> {
    try {
      this.isLoading.set(true);
      this.error.set(null);

      if (!this.supabaseClient) await this.initializeSupabaseClient();

      const { data, error } = await this.supabaseClient!
        .from('farms')
        .insert({
          user_id: userId,
          ...farmData,
          created_at: new Date().toISOString(),
        })
        .select()
        .single();

      if (error) throw error;

      // Reload farms
      await this.loadFarms(userId);
      console.log('✅ Farm created:', data);
      return data;
    } catch (error: any) {
      console.error('❌ Error creating farm:', error);
      this.error.set(error.message || 'Failed to create farm');
      return null;
    } finally {
      this.isLoading.set(false);
    }
  }

  /**
   * Update a farm
   */
  async updateFarm(farmId: string, updates: Partial<Farm>): Promise<boolean> {
    try {
      this.isLoading.set(true);
      this.error.set(null);

      if (!this.supabaseClient) await this.initializeSupabaseClient();

      const { error } = await this.supabaseClient!
        .from('farms')
        .update(updates)
        .eq('id', farmId);

      if (error) throw error;

      // Update local signal
      const updatedFarms = this.farms().map(f => 
        f.id === farmId ? { ...f, ...updates } : f
      );
      this.farms.set(updatedFarms);

      console.log('✅ Farm updated');
      return true;
    } catch (error: any) {
      console.error('❌ Error updating farm:', error);
      this.error.set(error.message || 'Failed to update farm');
      return false;
    } finally {
      this.isLoading.set(false);
    }
  }

  // ========================================================================
  // CROPS METHODS
  // ========================================================================

  /**
   * Load crops for a farm
   */
  async loadCrops(farmId: string): Promise<Crop[]> {
    try {
      this.isLoading.set(true);
      this.error.set(null);

      if (!this.supabaseClient) await this.initializeSupabaseClient();

      const { data, error } = await this.supabaseClient!
        .from('crops')
        .select('*')
        .eq('farm_id', farmId)
        .order('created_at', { ascending: false });

      if (error) throw error;

      this.crops.set(data || []);
      console.log(`✅ Loaded ${data?.length || 0} crops`);
      return data || [];
    } catch (error: any) {
      console.error('❌ Error loading crops:', error);
      this.error.set(error.message || 'Failed to load crops');
      return [];
    } finally {
      this.isLoading.set(false);
    }
  }

  /**
   * Create a new crop
   */
  async createCrop(farmId: string, cropData: Partial<Crop>): Promise<Crop | null> {
    try {
      this.isLoading.set(true);
      this.error.set(null);

      if (!this.supabaseClient) await this.initializeSupabaseClient();

      const { data, error } = await this.supabaseClient!
        .from('crops')
        .insert({
          farm_id: farmId,
          ...cropData,
          status: 'active',
          created_at: new Date().toISOString(),
        })
        .select()
        .single();

      if (error) throw error;

      // Reload crops
      await this.loadCrops(farmId);
      console.log('✅ Crop created:', data);
      return data;
    } catch (error: any) {
      console.error('❌ Error creating crop:', error);
      this.error.set(error.message || 'Failed to create crop');
      return null;
    } finally {
      this.isLoading.set(false);
    }
  }

  // ========================================================================
  // WORKERS METHODS
  // ========================================================================

  /**
   * Load workers for a farm
   */
  async loadWorkers(farmId: string): Promise<WorkerProfile[]> {
    try {
      this.isLoading.set(true);
      this.error.set(null);

      if (!this.supabaseClient) await this.initializeSupabaseClient();

      const { data, error } = await this.supabaseClient!
        .from('worker_profiles')
        .select('*')
        .eq('farm_id', farmId)
        .order('created_at', { ascending: false });

      if (error) throw error;

      this.workers.set(data || []);
      console.log(`✅ Loaded ${data?.length || 0} workers`);
      return data || [];
    } catch (error: any) {
      console.error('❌ Error loading workers:', error);
      this.error.set(error.message || 'Failed to load workers');
      return [];
    } finally {
      this.isLoading.set(false);
    }
  }

  // ========================================================================
  // ANALYTICS METHODS
  // ========================================================================

  /**
   * Calculate dashboard analytics
   */
  calculateAnalytics(): void {
    const analytics: DashboardAnalyticsData = {
      totalFarms: this.farms().length,
      totalCrops: this.crops().length,
      activeCrops: this.activeCrops().length,
      totalWorkers: this.workers().length,
      activeWorkers: this.activeWorkers().length,
      totalFarmSize: this.totalFarmSize(),
      lastUpdated: new Date().toISOString(),
    };

    this.analytics.set(analytics);
    console.log('✅ Analytics calculated:', analytics);
  }

  /**
   * Fetch credit score from backend
   */
  async fetchCreditScore(userId: string): Promise<CreditScore | null> {
    try {
      this.isLoading.set(true);

      const response = await this.http.get<CreditScore>(
        `${this.apiUrl}/farmscore/score/${userId}`
      ).toPromise();

      if (response) {
        this.creditScore.set(response);
        console.log('✅ Credit score loaded:', response);
        return response;
      }
      return null;
    } catch (error: any) {
      console.error('❌ Error fetching credit score:', error);
      return null;
    } finally {
      this.isLoading.set(false);
    }
  }

  // ========================================================================
  // REAL-TIME SUBSCRIPTIONS
  // ========================================================================

  /**
   * Subscribe to farm updates
   */
  subscribeToCropUpdates(farmId: string): void {
    if (!this.supabaseClient) return;

    const cropsChannel = this.supabaseClient
      .channel(`crops:farm_id=eq.${farmId}`)
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'crops', filter: `farm_id=eq.${farmId}` },
        (payload: any) => {
          console.log('📨 Crop update received:', payload);
          this.loadCrops(farmId);
        }
      )
      .subscribe();
  }

  /**
   * Subscribe to worker updates
   */
  subscribeToWorkerUpdates(farmId: string): void {
    if (!this.supabaseClient) return;

    const workersChannel = this.supabaseClient
      .channel(`workers:farm_id=eq.${farmId}`)
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'worker_profiles', filter: `farm_id=eq.${farmId}` },
        (payload: any) => {
          console.log('📨 Worker update received:', payload);
          this.loadWorkers(farmId);
        }
      )
      .subscribe();
  }
}
