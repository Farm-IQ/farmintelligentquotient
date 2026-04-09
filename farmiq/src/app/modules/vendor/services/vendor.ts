import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { SupabaseService } from '../../auth/services/supabase';
import { inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface VendorProfile {
  id: string;
  userId: string;
  businessName: string;
  businessType?: string;
  registrationNumber?: string;
  taxId?: string;
  address?: string;
  city?: string;
  state?: string;
  zipCode?: string;
  phoneNumber?: string;
  businessDescription?: string;
  averageRating?: number;
  createdAt?: string;
  updatedAt?: string;
}

export interface VendorProduct {
  id: string;
  vendorId: string;
  name: string;
  description: string;
  category: string;
  price: number;
  quantity: number;
  images?: string[];
  specifications?: Record<string, any>;
  createdAt?: string;
  updatedAt?: string;
}

export interface VendorOrder {
  id: string;
  vendorId: string;
  buyerId: string;
  productIds: string[];
  totalAmount: number;
  status: 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';
  createdAt?: string;
  updatedAt?: string;
}

@Injectable({
  providedIn: 'root',
})
export class VendorService {
  private apiUrl = '/api/vendor';

  private http = inject(HttpClient);
  private supabaseService = inject(SupabaseService);

  constructor(
  ) {}

  /**
   * Get vendor profile
   */
  getVendorProfile(vendorId: string): Observable<VendorProfile> {
    return this.http.get<VendorProfile>(`${this.apiUrl}/${vendorId}`);
  }

  /**
   * Update vendor profile
   */
  updateVendorProfile(vendorId: string, profile: Partial<VendorProfile>): Observable<VendorProfile> {
    return this.http.patch<VendorProfile>(`${this.apiUrl}/${vendorId}`, profile);
  }

  /**
   * Get all products for vendor
   */
  getVendorProducts(vendorId: string): Observable<VendorProduct[]> {
    return this.http.get<VendorProduct[]>(`${this.apiUrl}/${vendorId}/products`);
  }

  /**
   * Add new product
   */
  addProduct(vendorId: string, product: Partial<VendorProduct>): Observable<VendorProduct> {
    return this.http.post<VendorProduct>(`${this.apiUrl}/${vendorId}/products`, product);
  }

  /**
   * Update product
   */
  updateProduct(vendorId: string, productId: string, product: Partial<VendorProduct>): Observable<VendorProduct> {
    return this.http.patch<VendorProduct>(`${this.apiUrl}/${vendorId}/products/${productId}`, product);
  }

  /**
   * Delete product
   */
  deleteProduct(vendorId: string, productId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${vendorId}/products/${productId}`);
  }

  /**
   * Get vendor orders
   */
  getVendorOrders(vendorId: string, status?: string): Observable<VendorOrder[]> {
    const params = status ? `?status=${status}` : '';
    return this.http.get<VendorOrder[]>(`${this.apiUrl}/${vendorId}/orders${params}`);
  }

  /**
   * Update order status
   */
  updateOrderStatus(vendorId: string, orderId: string, status: string): Observable<VendorOrder> {
    return this.http.patch<VendorOrder>(`${this.apiUrl}/${vendorId}/orders/${orderId}`, { status });
  }

  /**
   * Get vendor analytics
   */
  getAnalytics(vendorId: string, period: string = 'month'): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${vendorId}/analytics?period=${period}`);
  }

  /**
   * Get vendor wallet balance
   */
  getWalletBalance(vendorId: string): Observable<{ balance: number; currency: string }> {
    return this.http.get<{ balance: number; currency: string }>(`${this.apiUrl}/${vendorId}/wallet`);
  }

  /**
   * Withdraw from wallet
   */
  withdrawFunds(vendorId: string, amount: number, accountDetails: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/${vendorId}/wallet/withdraw`, {
      amount,
      accountDetails
    });
  }

  /**
   * Get user profile for navbar
   */
  getUserProfile(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/profile`);
  }

  /**
   * Get notifications for navbar
   */
  getNotifications(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/notifications`);
  }

  /**
   * Mark all notifications as read
   */
  markNotificationsAsRead(): Observable<{ status: string }> {
    return this.http.post<{ status: string }>(`${this.apiUrl}/notifications/mark-all-read`, {});
  }

  /**
   * Mark single notification as read
   */
  markNotificationAsRead(notificationId: string): Observable<{ status: string }> {
    return this.http.post<{ status: string }>(`${this.apiUrl}/notifications/${notificationId}/read`, {});
  }

  /**
   * Delete a notification
   */
  deleteNotification(notificationId: string): Observable<{ status: string }> {
    return this.http.delete<{ status: string }>(`${this.apiUrl}/notifications/${notificationId}`);
  }

  /**
   * Logout
   */
  logout(): Observable<{ status: string }> {
    return this.http.post<{ status: string }>(`${this.apiUrl}/logout`, {});
  }
}
