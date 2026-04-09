/**
 * FARMER API SERVICE
 * Service wrapper for farmer-specific API calls
 * 
 * Uses core interceptors automatically (apiInterceptor, errorInterceptor)
 * All HTTP requests made through HttpClient get:
 * - Authorization header (JWT token)
 * - X-FarmIQ-ID header
 * - X-User-Role header
 * - Global error handling
 */

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class FarmerApiService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/api/farmer`;

  /**
   * Get farmer profile
   */
  getFarmerProfile(farmerId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/profile/${farmerId}`);
  }

  /**
   * Update farmer profile
   */
  updateFarmerProfile(farmerId: string, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/profile/${farmerId}`, data);
  }

  /**
   * Get farm data
   */
  getFarmData(farmId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/farms/${farmId}`);
  }

  /**
   * Get all farms for farmer
   */
  getAllFarms(farmerId: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/farms`);
  }

  /**
   * Create new farm
   */
  createFarm(farmData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/farms`, farmData);
  }

  /**
   * Get livestock data
   */
  getLivestock(farmId: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/farms/${farmId}/livestock`);
  }

  /**
   * Get farm crops
   */
  getCrops(farmId: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/farms/${farmId}/crops`);
  }

  /**
   * Get financial data
   */
  getFinancials(farmId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/farms/${farmId}/financials`);
  }
}
