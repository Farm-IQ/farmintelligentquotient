import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import { FarmInventory, InventoryTransaction, InventoryCategory } from '../models/livestock-operations.models';

/**
 * InventoryManagementService
 * Manages farm inventory including stock tracking, transactions, and reorder management
 */
@Injectable({
  providedIn: 'root'
})
export class InventoryManagementService {
  private apiUrl = '/api/inventory';
  private inventorySubject = new BehaviorSubject<FarmInventory[]>([]);
  public inventory$ = this.inventorySubject.asObservable();

  private transactionsSubject = new BehaviorSubject<InventoryTransaction[]>([]);
  public transactions$ = this.transactionsSubject.asObservable();

  private categoriesSubject = new BehaviorSubject<InventoryCategory[]>([]);
  public categories$ = this.categoriesSubject.asObservable();

  private lowStockAlertsSubject = new BehaviorSubject<FarmInventory[]>([]);
  public lowStockAlerts$ = this.lowStockAlertsSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Get inventory categories for dropdown population
   */
  getInventoryCategories(): Observable<InventoryCategory[]> {
    return this.http.get<InventoryCategory[]>(`${this.apiUrl}/categories`).pipe(
      tap(categories => {
        this.categoriesSubject.next(categories);
        console.log(`✅ Loaded ${categories.length} inventory categories`);
      }),
      catchError(err => throwError(() => new Error(`Failed to load inventory categories: ${err.message}`)))
    );
  }

  /**
   * Get all inventory items for a farm
   */
  getFarmInventory(farmId: string): Observable<FarmInventory[]> {
    return this.http.get<FarmInventory[]>(`${this.apiUrl}/farms/${farmId}`).pipe(
      tap(inventory => {
        this.inventorySubject.next(inventory);
        this.updateLowStockAlerts(inventory);
        console.log(`✅ Loaded ${inventory.length} inventory items for farm ${farmId}`);
      }),
      catchError(err => throwError(() => new Error(`Failed to load inventory: ${err.message}`)))
    );
  }

  /**
   * Get specific inventory item details
   */
  getInventoryItem(itemId: string): Observable<FarmInventory> {
    return this.http.get<FarmInventory>(`${this.apiUrl}/items/${itemId}`).pipe(
      catchError(err => throwError(() => new Error(`Failed to load inventory item: ${err.message}`)))
    );
  }

  /**
   * Create new inventory item
   */
  createInventoryItem(farmId: string, item: Partial<FarmInventory>): Observable<FarmInventory> {
    return this.http.post<FarmInventory>(`${this.apiUrl}/farms/${farmId}`, item).pipe(
      tap(created => {
        const current = this.inventorySubject.value;
        this.inventorySubject.next([...current, created]);
        console.log(`✅ Inventory item created: ${created.itemName}`);
      }),
      catchError(err => throwError(() => new Error(`Failed to create inventory item: ${err.message}`)))
    );
  }

  /**
   * Update inventory item (e.g., reorder level, supplier)
   */
  updateInventoryItem(itemId: string, updates: Partial<FarmInventory>): Observable<FarmInventory> {
    return this.http.patch<FarmInventory>(`${this.apiUrl}/items/${itemId}`, updates).pipe(
      tap(updated => {
        const current = this.inventorySubject.value;
        const index = current.findIndex(i => i.id === itemId);
        if (index > -1) {
          current[index] = updated;
          this.inventorySubject.next([...current]);
          this.updateLowStockAlerts(current);
        }
        console.log(`✅ Inventory item updated: ${updated.itemName}`);
      }),
      catchError(err => throwError(() => new Error(`Failed to update inventory item: ${err.message}`)))
    );
  }

  /**
   * Delete inventory item
   */
  deleteInventoryItem(itemId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/items/${itemId}`).pipe(
      tap(() => {
        const current = this.inventorySubject.value;
        const filtered = current.filter(i => i.id !== itemId);
        this.inventorySubject.next(filtered);
        console.log(`✅ Inventory item deleted: ${itemId}`);
      }),
      catchError(err => throwError(() => new Error(`Failed to delete inventory item: ${err.message}`)))
    );
  }

  /**
   * Record inventory transaction (purchase, use, sale, damage, adjustment)
   */
  recordTransaction(itemId: string, transaction: Partial<InventoryTransaction>): Observable<InventoryTransaction> {
    return this.http.post<InventoryTransaction>(`${this.apiUrl}/items/${itemId}/transactions`, transaction).pipe(
      tap(created => {
        const current = this.transactionsSubject.value;
        this.transactionsSubject.next([...current, created]);
        console.log(`✅ Transaction recorded: ${created.transactionType} of ${created.quantityChanged} units`);
      }),
      catchError(err => throwError(() => new Error(`Failed to record transaction: ${err.message}`)))
    );
  }

  /**
   * Get transaction history for an inventory item
   */
  getTransactionHistory(itemId: string, filters?: { startDate?: string; endDate?: string; transactionType?: string }): Observable<InventoryTransaction[]> {
    let url = `${this.apiUrl}/items/${itemId}/transactions`;
    if (filters) {
      const params = new URLSearchParams();
      if (filters.startDate) params.append('startDate', filters.startDate);
      if (filters.endDate) params.append('endDate', filters.endDate);
      if (filters.transactionType) params.append('transactionType', filters.transactionType);
      if (params.toString()) url += `?${params.toString()}`;
    }
    return this.http.get<InventoryTransaction[]>(url).pipe(
      tap(transactions => this.transactionsSubject.next(transactions)),
      catchError(err => throwError(() => new Error(`Failed to load transaction history: ${err.message}`)))
    );
  }

  /**
   * Get low stock alerts (items below reorder level)
   */
  getLowStockItems(farmId: string): Observable<FarmInventory[]> {
    return this.http.get<FarmInventory[]>(`${this.apiUrl}/farms/${farmId}/low-stock`).pipe(
      tap(items => {
        this.lowStockAlertsSubject.next(items);
        console.log(`⚠️ ${items.length} items below reorder level`);
      }),
      catchError(err => throwError(() => new Error(`Failed to load low stock items: ${err.message}`)))
    );
  }

  /**
   * Perform stock take (reconcile physical count with system count)
   */
  performStockTake(itemId: string, physicalCount: number, notes?: string): Observable<InventoryTransaction> {
    return this.http.post<InventoryTransaction>(`${this.apiUrl}/items/${itemId}/stock-take`, {
      physicalCount,
      notes
    }).pipe(
      tap(result => {
        console.log(`✅ Stock take completed: ${result.quantityChanged} unit adjustment`);
      }),
      catchError(err => throwError(() => new Error(`Failed to complete stock take: ${err.message}`)))
    );
  }

  /**
   * Get inventory summary with value analysis
   */
  getInventorySummary(farmId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/farms/${farmId}/summary`).pipe(
      catchError(err => throwError(() => new Error(`Failed to load inventory summary: ${err.message}`)))
    );
  }

  /**
   * Export inventory report
   */
  exportInventoryReport(farmId: string, format: 'csv' | 'pdf' = 'csv'): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/farms/${farmId}/export?format=${format}`, { responseType: 'blob' }).pipe(
      catchError(err => throwError(() => new Error(`Failed to export inventory report: ${err.message}`)))
    );
  }

  /**
   * Helper: Update low stock alerts
   */
  private updateLowStockAlerts(inventory: FarmInventory[]): void {
    const lowStockItems = inventory.filter(item => 
      item.currentQuantity <= (item.reorderLevel || 0)
    );
    this.lowStockAlertsSubject.next(lowStockItems);
    if (lowStockItems.length > 0) {
      console.warn(`⚠️ ${lowStockItems.length} items below reorder level`);
    }
  }

  /**
   * Helper: Calculate inventory value
   */
  calculateInventoryValue(inventory: FarmInventory[]): number {
    return inventory.reduce((total, item) => {
      const itemValue = (item.currentQuantity || 0) * (item.unitCost || 0);
      return total + itemValue;
    }, 0);
  }
}
