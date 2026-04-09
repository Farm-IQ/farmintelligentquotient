/**
 * AGENT API SERVICE
 * Service wrapper for agent-specific API calls
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
export class AgentApiService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/api/agent`;

  /**
   * Get agent profile
   */
  getAgentProfile(agentId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/profile/${agentId}`);
  }

  /**
   * Update agent profile
   */
  updateAgentProfile(agentId: string, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/profile/${agentId}`, data);
  }

  /**
   * Get agent's assigned clients
   */
  getClients(agentId: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/clients`);
  }

  /**
   * Get client details
   */
  getClientDetails(clientId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/clients/${clientId}`);
  }

  /**
   * Get agent's performance metrics
   */
  getPerformanceMetrics(): Observable<any> {
    return this.http.get(`${this.apiUrl}/performance`);
  }

  /**
   * Get current commissions/earnings
   */
  getEarnings(): Observable<any> {
    return this.http.get(`${this.apiUrl}/earnings`);
  }

  /**
   * Submit transaction
   */
  submitTransaction(transactionData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/transactions`, transactionData);
  }
}
