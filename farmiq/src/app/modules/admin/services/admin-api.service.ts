/**
 * ADMIN API SERVICE
 * Service wrapper for admin-specific API calls
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
export class AdminApiService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/api/admin`;

  /**
   * Get dashboard statistics
   */
  getDashboardStats(): Observable<any> {
    return this.http.get(`${this.apiUrl}/dashboard/stats`);
  }

  /**
   * Get all users
   */
  getAllUsers(filters?: any): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/users`, { params: filters });
  }

  /**
   * Get user details
   */
  getUserDetails(userId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/users/${userId}`);
  }

  /**
   * Block/Unblock user
   */
  toggleUserStatus(userId: string, status: boolean): Observable<any> {
    return this.http.put(`${this.apiUrl}/users/${userId}/status`, { active: status });
  }

  /**
   * Get system logs
   */
  getSystemLogs(filters?: any): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/logs`, { params: filters });
  }

  /**
   * Get role assignments
   */
  getRoleAssignments(userId?: string): Observable<any[]> {
    const params: any = userId ? { userId } : undefined;
    return this.http.get<any[]>(`${this.apiUrl}/roles/assignments`, { params });
  }

  /**
   * Assign role to user
   */
  assignRole(userId: string, role: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/roles/assign`, { userId, role });
  }

  /**
   * Revoke role from user
   */
  revokeRole(userId: string, role: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/roles/revoke`, { userId, role });
  }
}
