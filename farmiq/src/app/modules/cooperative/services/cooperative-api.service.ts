/**
 * COOPERATIVE API SERVICE
 * Service wrapper for cooperative-specific API calls
 * 
 * Uses core interceptors automatically (apiInterceptor, errorInterceptor)
 * All HTTP requests include auth headers and error handling
 */

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class CooperativeApiService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/api/cooperative`;

  /**
   * Get cooperative profile
   */
  getCooperativeProfile(cooperativeId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/profile/${cooperativeId}`);
  }

  /**
   * Update cooperative profile
   */
  updateCooperativeProfile(cooperativeId: string, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/profile/${cooperativeId}`, data);
  }

  /**
   * Get members
   */
  getMembers(cooperativeId: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/${cooperativeId}/members`);
  }

  /**
   * Add member to cooperative
   */
  addMember(cooperativeId: string, memberId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/${cooperativeId}/members`, { memberId });
  }

  /**
   * Remove member from cooperative
   */
  removeMember(cooperativeId: string, memberId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${cooperativeId}/members/${memberId}`);
  }

  /**
   * Get cooperative transactions
   */
  getTransactions(cooperativeId: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/${cooperativeId}/transactions`);
  }

  /**
   * Get bulk discounts available to cooperative
   */
  getBulkDiscounts(cooperativeId: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/${cooperativeId}/discounts`);
  }
}
