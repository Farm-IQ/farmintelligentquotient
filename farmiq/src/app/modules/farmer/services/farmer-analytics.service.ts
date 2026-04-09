/**
 * Farmer Analytics Service
 * Handles analytics calculations: yield metrics, soil health, weather impact, recommendations
 */

import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';

export interface YieldMetrics {
  currentSeason: number;
  lastSeason: number;
  average: number;
  percentChange: number;
  trend: 'up' | 'down' | 'stable';
}

export interface SoilHealthData {
  npk: { nitrogen: number; phosphorus: number; potassium: number };
  ph: number;
  organicMatter: number;
  moistureLevel: number;
  lastTestedDate: string;
  recommendation: string;
}

export interface WeatherImpact {
  temperature: number;
  rainfall: number;
  humidity: number;
  windSpeed: number;
  uvIndex: number;
  plantStressLevel: 'low' | 'medium' | 'high';
  impact: string;
}

export interface FarmAnalytics {
  period: 'weekly' | 'monthly' | 'seasonal';
  yieldMetrics: YieldMetrics;
  soilHealth: SoilHealthData;
  weatherImpact: WeatherImpact;
  recommendations: string[];
  generateDate: string;
}

@Injectable({ providedIn: 'root' })
export class FarmerAnalyticsService {
  private apiUrl = environment.apiUrl;
  private supabaseUrl = `${environment.supabase.url}/rest/v1`;

  // ========== STATE ==========
  analytics = signal<FarmAnalytics | null>(null);
  yieldHistory = signal<YieldMetrics[]>([]);
  soilHealthHistory = signal<SoilHealthData[]>([]);
  weatherHistory = signal<WeatherImpact[]>([]);
  loading = signal<boolean>(false);
  error = signal<string | null>(null);

  // ========== COMPUTED VALUES ==========
  yieldTrend = computed(() => this.analytics()?.yieldMetrics.trend || 'stable');
  averageYield = computed(() => this.analytics()?.yieldMetrics.average || 0);
  soilHealthStatus = computed(() => this.getSoilHealthStatus(this.analytics()?.soilHealth));
  weatherRisk = computed(() => this.analytics()?.weatherImpact.plantStressLevel || 'low');
  criticalRecommendations = computed(() => {
    return this.analytics()?.recommendations.filter(r => r.includes('URGENT')) || [];
  });

  constructor(private http: HttpClient) {}

  /**
   * Get complete analytics for a farm
   */
  getAnalytics(farmId: string, period: 'weekly' | 'monthly' | 'seasonal' = 'monthly'): Observable<FarmAnalytics> {
    this.loading.set(true);
    return this.http.get<FarmAnalytics>(
      `${this.apiUrl}/farms/${farmId}/analytics?period=${period}`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((data: FarmAnalytics) => {
        this.analytics.set(data);
        this.loading.set(false);
        this.error.set(null);
      }),
      catchError((err) => this.handleError('Failed to fetch analytics', err))
    );
  }

  /**
   * Get yield metrics with trend analysis
   */
  getYieldMetrics(farmId: string): Observable<YieldMetrics> {
    return this.http.get<YieldMetrics>(
      `${this.apiUrl}/farms/${farmId}/yield-metrics`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((metrics: YieldMetrics) => {
        // Calculate percentage change
        const change = ((metrics.currentSeason - metrics.lastSeason) / metrics.lastSeason) * 100;
        metrics.percentChange = Math.round(change * 100) / 100;
        
        // Determine trend
        if (change > 5) metrics.trend = 'up';
        else if (change < -5) metrics.trend = 'down';
        else metrics.trend = 'stable';
      }),
      catchError((err) => this.handleError('Failed to fetch yield metrics', err))
    );
  }

  /**
   * Get soil health data with NPK analysis
   */
  getSoilHealthData(farmId: string): Observable<SoilHealthData> {
    return this.http.get<SoilHealthData>(
      `${this.apiUrl}/farms/${farmId}/soil-health`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((data: SoilHealthData) => {
        // Generate recommendation based on NPK levels
        data.recommendation = this.generateSoilRecommendation(data);
      }),
      catchError((err) => this.handleError('Failed to fetch soil health', err))
    );
  }

  /**
   * Get weather impact on farm
   */
  getWeatherImpact(farmId: string): Observable<WeatherImpact> {
    return this.http.get<WeatherImpact>(
      `${this.apiUrl}/farms/${farmId}/weather-impact`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((data: WeatherImpact) => {
        // Assess plant stress level based on weather
        data.plantStressLevel = this.assessPlantStress(data);
        data.impact = this.generateWeatherImpact(data);
      }),
      catchError((err) => this.handleError('Failed to fetch weather impact', err))
    );
  }

  /**
   * Get AI-generated recommendations
   */
  getRecommendations(farmId: string): Observable<string[]> {
    return this.http.get<string[]>(
      `${this.apiUrl}/farms/${farmId}/recommendations`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((recs: string[]) => {
        const currentAnalytics = this.analytics();
        if (currentAnalytics) {
          currentAnalytics.recommendations = recs;
          this.analytics.set(currentAnalytics);
        }
      }),
      catchError((err) => this.handleError('Failed to fetch recommendations', err))
    );
  }

  /**
   * Get yield history for chart
   */
  getYieldHistory(farmId: string, months: number = 12): Observable<YieldMetrics[]> {
    return this.http.get<YieldMetrics[]>(
      `${this.apiUrl}/farms/${farmId}/yield-history?months=${months}`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((history: YieldMetrics[]) => {
        this.yieldHistory.set(history);
      }),
      catchError((err) => this.handleError('Failed to fetch yield history', err))
    );
  }

  /**
   * Get soil health history for trend
   */
  getSoilHealthHistory(farmId: string, months: number = 12): Observable<SoilHealthData[]> {
    return this.http.get<SoilHealthData[]>(
      `${this.apiUrl}/farms/${farmId}/soil-history?months=${months}`,
      { headers: this.getHeaders() }
    ).pipe(
      tap((history: SoilHealthData[]) => {
        this.soilHealthHistory.set(history);
      }),
      catchError((err) => this.handleError('Failed to fetch soil history', err))
    );
  }

  /**
   * LOGIC: Generate soil recommendation based on NPK levels
   */
  private generateSoilRecommendation(data: SoilHealthData): string {
    const { npk, ph, organicMatter } = data;
    const recommendations: string[] = [];

    // NPK Analysis
    if (npk.nitrogen < 20) recommendations.push('URGENT: Apply nitrogen fertilizer');
    else if (npk.nitrogen > 40) recommendations.push('Reduce nitrogen application');

    if (npk.phosphorus < 15) recommendations.push('Apply phosphorus supplement');
    if (npk.potassium < 10) recommendations.push('Apply potassium fertilizer');

    // pH Analysis
    if (ph < 6) recommendations.push('Soil is too acidic - add lime');
    else if (ph > 7.5) recommendations.push('Soil is too alkaline - add sulfur');

    // Organic Matter
    if (organicMatter < 2) recommendations.push('Increase organic matter with compost');

    return recommendations.length > 0 
      ? recommendations.join('; ') 
      : 'Soil health is optimal';
  }

  /**
   * LOGIC: Assess plant stress level based on weather conditions
   */
  private assessPlantStress(weather: WeatherImpact): 'low' | 'medium' | 'high' {
    let stressScore = 0;

    // Temperature stress (optimal: 15-30°C)
    if (weather.temperature < 10 || weather.temperature > 35) stressScore += 3;
    else if (weather.temperature < 15 || weather.temperature > 30) stressScore += 1;

    // Humidity stress (optimal: 50-80%)
    if (weather.humidity < 30 || weather.humidity > 90) stressScore += 3;
    else if (weather.humidity < 40 || weather.humidity > 85) stressScore += 1;

    // Wind stress
    if (weather.windSpeed > 30) stressScore += 3; // >30 km/h
    else if (weather.windSpeed > 20) stressScore += 1;

    // Rainfall stress (depends on season, but consistent rain is good)
    // Zero rainfall is bad

    // UV stress
    if (weather.uvIndex > 8) stressScore += 2;

    if (stressScore >= 5) return 'high';
    if (stressScore >= 2) return 'medium';
    return 'low';
  }

  /**
   * LOGIC: Generate human-readable weather impact message
   */
  private generateWeatherImpact(weather: WeatherImpact): string {
    const impacts: string[] = [];

    if (weather.temperature > 35) impacts.push('High heat risk - increase irrigation');
    if (weather.temperature < 10) impacts.push('Frost risk - protect young plants');
    if (weather.humidity < 30) impacts.push('Dry air - increase watering frequency');
    if (weather.humidity > 85) impacts.push('High humidity - monitor for fungal diseases');
    if (weather.windSpeed > 30) impacts.push('Strong winds - shelter may be needed');
    if (weather.uvIndex > 8) impacts.push('High UV - protect sensitive crops');
    if (weather.rainfall === 0) impacts.push('No rain expected - plan irrigation');

    return impacts.length > 0 
      ? impacts.join('; ') 
      : 'Weather conditions are favorable';
  }

  /**
   * Determine soil health status
   */
  private getSoilHealthStatus(soilData: SoilHealthData | null | undefined): string {
    if (!soilData) return 'unknown';

    const { npk, ph, organicMatter } = soilData;
    let healthScore = 0;

    // Score based on NPK (max 30 points)
    healthScore += Math.min((npk.nitrogen / 40) * 10, 10);
    healthScore += Math.min((npk.phosphorus / 30) * 10, 10);
    healthScore += Math.min((npk.potassium / 20) * 10, 10);

    // Score based on pH (max 20 points) - optimal 6.5-7
    if (soilData.ph >= 6 && soilData.ph <= 7.5) healthScore += 20;
    else if (soilData.ph >= 5.5 && soilData.ph <= 8) healthScore += 10;

    // Score based on organic matter (max 20 points) - optimal > 3%
    healthScore += Math.min((organicMatter / 4) * 20, 20);

    if (healthScore >= 70) return 'excellent';
    if (healthScore >= 50) return 'good';
    if (healthScore >= 30) return 'fair';
    return 'poor';
  }

  /**
   * Get HTTP headers with auth
   */
  private getHeaders() {
    const token = sessionStorage.getItem('auth_token');
    return {
      'Authorization': `Bearer ${token || ''}`,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Handle errors
   */
  private handleError(message: string, error: any) {
    console.error(message, error);
    this.error.set(message);
    this.loading.set(false);
    return throwError(() => error);
  }
}
