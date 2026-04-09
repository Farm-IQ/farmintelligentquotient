/**
 * LENDER API SERVICE
 * Service wrapper for lender-specific API calls
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
export class LenderApiService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/api/lender`;

  /**
   * Get lender profile
   */
  getLenderProfile(lenderId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/profile/${lenderId}`);
  }

  /**
   * Update lender profile
   */
  updateLenderProfile(lenderId: string, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/profile/${lenderId}`, data);
  }

  /**
   * Get active loans
   */
  getActiveLoans(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/loans`);
  }

  /**
   * Get loan applications
   */
  getLoanApplications(filters?: any): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/applications`, { params: filters });
  }

  /**
   * Get loan details
   */
  getLoanDetails(loanId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/loans/${loanId}`);
  }

  /**
   * Approve loan application
   */
  approveLoan(applicationId: string, terms: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/applications/${applicationId}/approve`, terms);
  }

  /**
   * Reject loan application
   */
  rejectLoan(applicationId: string, reason: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/applications/${applicationId}/reject`, { reason });
  }

  /**
   * Get portfolio performance
   */
  getPortfolioPerformance(): Observable<any> {
    return this.http.get(`${this.apiUrl}/portfolio/performance`);
  }
}
