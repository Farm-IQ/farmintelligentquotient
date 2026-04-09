/**
 * WORKER API SERVICE
 * Service wrapper for worker-specific API calls
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
export class WorkerApiService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/api/worker`;

  /**
   * Get worker profile
   */
  getWorkerProfile(workerId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/profile/${workerId}`);
  }

  /**
   * Update worker profile
   */
  updateWorkerProfile(workerId: string, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/profile/${workerId}`, data);
  }

  /**
   * Get assigned tasks
   */
  getAssignedTasks(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/tasks`);
  }

  /**
   * Get task details
   */
  getTaskDetails(taskId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/tasks/${taskId}`);
  }

  /**
   * Update task status
   */
  updateTaskStatus(taskId: string, status: string): Observable<any> {
    return this.http.put(`${this.apiUrl}/tasks/${taskId}/status`, { status });
  }

  /**
   * Submit work report
   */
  submitWorkReport(taskId: string, reportData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/tasks/${taskId}/report`, reportData);
  }

  /**
   * Get earnings/payments
   */
  getEarnings(): Observable<any> {
    return this.http.get(`${this.apiUrl}/earnings`);
  }

  /**
   * Get work history
   */
  getWorkHistory(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/history`);
  }
}
