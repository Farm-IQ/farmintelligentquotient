/**
 * VENDOR API SERVICE
 * Service wrapper for vendor-specific API calls
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
export class VendorApiService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/api/vendor`;

  /**
   * Get vendor profile
   */
  getVendorProfile(vendorId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/profile/${vendorId}`);
  }

  /**
   * Update vendor profile
   */
  updateVendorProfile(vendorId: string, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/profile/${vendorId}`, data);
  }

  /**
   * Get products/services
   */
  getProducts(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/products`);
  }

  /**
   * Create new product/service
   */
  createProduct(productData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/products`, productData);
  }

  /**
   * Update product
   */
  updateProduct(productId: string, productData: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/products/${productId}`, productData);
  }

  /**
   * Delete product
   */
  deleteProduct(productId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/products/${productId}`);
  }

  /**
   * Get sales/orders
   */
  getOrders(filters?: any): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/orders`, { params: filters });
  }

  /**
   * Get sales analytics
   */
  getSalesAnalytics(period?: string): Observable<any> {
    const options = period ? { params: { period } } : {};
    return this.http.get(`${this.apiUrl}/analytics`, options);
  }
}
