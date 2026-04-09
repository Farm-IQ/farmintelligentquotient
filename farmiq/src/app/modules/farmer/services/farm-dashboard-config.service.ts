import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError, of } from 'rxjs';
import { tap, catchError, map } from 'rxjs/operators';
import { FarmDashboardConfig, DashboardModule } from '../models/livestock-operations.models';

/**
 * FarmDashboardConfigService
 * Manages dynamic dashboard module selection and configuration based on farm operations
 */
@Injectable({
  providedIn: 'root'
})
export class FarmDashboardConfigService {
  private apiUrl = '/api/dashboard';
  private configSubject = new BehaviorSubject<FarmDashboardConfig | null>(null);
  public config$ = this.configSubject.asObservable();

  private availableModulesSubject = new BehaviorSubject<DashboardModule[]>([]);
  public availableModules$ = this.availableModulesSubject.asObservable();

  private activeModulesSubject = new BehaviorSubject<DashboardModule[]>([]);
  public activeModules$ = this.activeModulesSubject.asObservable();

  constructor(private http: HttpClient) {
    this.initializeModules();
  }

  /**
   * Initialize all available dashboard modules
   */
  private initializeModules(): void {
    const allModules: DashboardModule[] = [
      {
        id: 'farm-overview',
        title: 'Farm Overview',
        name: 'Farm Overview',
        description: 'Summary of all farm operations and metrics',
        icon: '🏡',
        category: 'general',
        componentName: 'FarmOverviewComponent',
        displayOrder: 1,
        position: 1,
        isRequired: true,
        enabled: true,
        component: 'FarmOverviewComponent',
        requiredOperations: []
      },
      {
        id: 'crop-management',
        title: 'Crop Management',
        name: 'Crop Management',
        description: 'Track crop production, planting schedules, and yields',
        icon: '🌾',
        category: 'crop',
        componentName: 'CropManagementComponent',
        displayOrder: 2,
        position: 2,
        isRequired: false,
        enabled: false,
        component: 'CropManagementComponent',
        requiredOperations: ['crop_production']
      },
      {
        id: 'coffee-operations',
        title: 'Coffee Operations',
        name: 'Coffee Operations',
        description: 'Coffee-specific management: paddocks, shade coverage, quality grading',
        icon: '☕',
        category: 'commodity',
        componentName: 'CoffeeOperationsComponent',
        displayOrder: 3,
        position: 3,
        isRequired: false,
        enabled: false,
        component: 'CoffeeOperationsComponent',
        requiredOperations: ['crop_production'],
        requiredCrops: ['coffee']
      },
      {
        id: 'dairy-management',
        title: 'Dairy Management',
        name: 'Dairy Management',
        description: 'Dairy cattle management, milk production, breeding records',
        icon: '🥛',
        category: 'livestock',
        componentName: 'DairyManagementComponent',
        displayOrder: 4,
        position: 4,
        isRequired: false,
        enabled: false,
        component: 'DairyManagementComponent',
        requiredOperations: ['livestock_dairy']
      },
      {
        id: 'livestock-operations',
        title: 'Livestock Management',
        name: 'Livestock Management',
        description: 'General livestock tracking, health records, production metrics',
        icon: '🐄',
        category: 'livestock',
        componentName: 'LivestockOperationsComponent',
        displayOrder: 5,
        position: 5,
        isRequired: false,
        enabled: false,
        component: 'LivestockOperationsComponent',
        requiredOperations: ['livestock_beef', 'livestock_poultry', 'livestock_aquaculture']
      },
      {
        id: 'inventory-management',
        title: 'Inventory & Stock',
        name: 'Inventory & Stock',
        description: 'Track farm inventory, stock levels, and reorder management',
        icon: '📦',
        category: 'operations',
        componentName: 'InventoryManagementComponent',
        displayOrder: 6,
        position: 6,
        isRequired: false,
        enabled: false,
        component: 'InventoryManagementComponent',
        requiredOperations: []
      },
      {
        id: 'financial-tracking',
        title: 'Financial Dashboard',
        name: 'Financial Dashboard',
        description: 'Costs, revenue, profitability analysis, and ROI tracking',
        icon: '💰',
        category: 'financial',
        componentName: 'FinancialDashboardComponent',
        displayOrder: 7,
        position: 7,
        isRequired: false,
        enabled: false,
        component: 'FinancialDashboardComponent',
        requiredOperations: []
      },
      {
        id: 'weather-forecast',
        title: 'Weather & Forecast',
        name: 'Weather & Forecast',
        description: 'Weather predictions, rainfall patterns, and climate impact',
        icon: '🌤️',
        category: 'information',
        componentName: 'WeatherForecastComponent',
        displayOrder: 8,
        position: 8,
        isRequired: false,
        enabled: false,
        component: 'WeatherForecastComponent',
        requiredOperations: []
      },
      {
        id: 'pest-disease',
        title: 'Pest & Disease Alert',
        name: 'Pest & Disease Alert',
        description: 'Monitor pests, diseases, and treatment recommendations',
        icon: '🐛',
        category: 'alerts',
        componentName: 'PestDiseaseAlertComponent',
        displayOrder: 9,
        position: 9,
        isRequired: false,
        enabled: false,
        component: 'PestDiseaseAlertComponent',
        requiredOperations: []
      },
      {
        id: 'market-prices',
        title: 'Market Prices',
        name: 'Market Prices',
        description: 'Track commodity prices and market trends',
        icon: '📈',
        category: 'market',
        componentName: 'MarketPricesComponent',
        displayOrder: 10,
        position: 10,
        isRequired: false,
        enabled: false,
        component: 'MarketPricesComponent',
        requiredOperations: []
      }
    ];
    this.availableModulesSubject.next(allModules);
  }

  /**
   * Get dashboard configuration for a farm
   */
  getFarmDashboardConfig(farmId: string): Observable<FarmDashboardConfig> {
    return this.http.get<FarmDashboardConfig>(`${this.apiUrl}/farms/${farmId}/config`).pipe(
      tap(config => {
        this.configSubject.next(config);
        this.updateActiveModules(config);
        console.log(`✅ Dashboard config loaded for farm ${farmId}`);
      }),
      catchError(err => {
        console.warn('Dashboard config not found, creating new config...');
        // Return default config if not found
        return this.createDefaultConfig(farmId);
      })
    );
  }

  /**
   * Create default dashboard configuration based on farm operations
   */
  private createDefaultConfig(farmId: string): Observable<FarmDashboardConfig> {
    // Get farm operations and determine which modules to enable
    return this.http.get<any>(`/api/farm-financial/farms/${farmId}/operations`).pipe(
      tap((operations: any) => {
        const config = this.generateConfigFromOperations(farmId, operations);
        this.configSubject.next(config);
        this.updateActiveModules(config);
      }),
      // Map the operations response to FarmDashboardConfig
      map((operations: any) => {
        const config = this.generateConfigFromOperations(farmId, operations);
        return config;
      }),
      catchError((err: any) => {
        // Fallback: enable only general modules
        const defaultConfig: FarmDashboardConfig = {
          farmId,
          enabledModuleIds: ['farm-overview', 'weather-forecast', 'market-prices'],
          moduleSettings: {},
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
        this.configSubject.next(defaultConfig);
        this.updateActiveModules(defaultConfig);
        return of(defaultConfig);
      })
    );
  }

  /**
   * Generate dashboard config based on available farm operations
   */
  private generateConfigFromOperations(farmId: string, operations: any[]): FarmDashboardConfig {
    const enabledModuleIds: string[] = ['farm-overview', 'weather-forecast', 'market-prices'];

    // Enable modules based on operations
    if (operations.some((op: any) => op.operationType === 'crop_production')) {
      enabledModuleIds.push('crop-management');
    }

    if (operations.some((op: any) => op.operationType === 'crop_production' && op.primaryCrop === 'coffee')) {
      enabledModuleIds.push('coffee-operations');
    }

    if (operations.some((op: any) => op.operationType === 'livestock_dairy')) {
      enabledModuleIds.push('dairy-management');
    }

    if (operations.some((op: any) => ['livestock_beef', 'livestock_poultry', 'livestock_aquaculture'].includes(op.operationType))) {
      enabledModuleIds.push('livestock-operations');
    }

    enabledModuleIds.push('inventory-management', 'financial-tracking', 'pest-disease');

    const config: FarmDashboardConfig = {
      farmId,
      enabledModuleIds,
      moduleSettings: {},
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    return config;
  }

  /**
   * Update or create dashboard configuration
   */
  saveDashboardConfig(config: FarmDashboardConfig): Observable<FarmDashboardConfig> {
    const isUpdate = config.id !== undefined;
    const endpoint = isUpdate ? `${this.apiUrl}/config/${config.id}` : `${this.apiUrl}/config`;
    const method = isUpdate ? 'patch' : 'post';

    return (method === 'patch' ?
      this.http.patch<FarmDashboardConfig>(endpoint, config) :
      this.http.post<FarmDashboardConfig>(endpoint, config)
    ).pipe(
      tap(updated => {
        this.configSubject.next(updated);
        this.updateActiveModules(updated);
        console.log(`✅ Dashboard config saved`);
      }),
      catchError(err => throwError(() => new Error(`Failed to save dashboard config: ${err.message}`)))
    );
  }

  /**
   * Enable a specific dashboard module
   */
  enableModule(moduleId: string): void {
    const config = this.configSubject.value;
    if (config) {
      if (!config.enabledModuleIds) {
        config.enabledModuleIds = [];
      }
      if (!config.enabledModuleIds.includes(moduleId)) {
        config.enabledModuleIds.push(moduleId);
        config.updatedAt = new Date().toISOString();
        this.configSubject.next(config);
        this.updateActiveModules(config);
        console.log(`✅ Module enabled: ${moduleId}`);
      }
    }
  }

  /**
   * Disable a specific dashboard module
   */
  disableModule(moduleId: string): void {
    const config = this.configSubject.value;
    if (config && config.enabledModuleIds) {
      config.enabledModuleIds = config.enabledModuleIds.filter((id: string) => id !== moduleId);
      config.updatedAt = new Date().toISOString();
      this.configSubject.next(config);
      this.updateActiveModules(config);
      console.log(`✅ Module disabled: ${moduleId}`);
    }
  }

  /**
   * Update active modules based on configuration
   */
  private updateActiveModules(config: FarmDashboardConfig): void {
    const allModules = this.availableModulesSubject.value;
    const enabledIds = config.enabledModuleIds || [];
    const activeModules = allModules.filter(module =>
      enabledIds.includes(module.id)
    ).sort((a, b) => (a.displayOrder || 0) - (b.displayOrder || 0));

    this.activeModulesSubject.next(activeModules);
    console.log(`📊 Active modules updated: ${activeModules.length} modules enabled`);
  }

  /**
   * Get modules by category
   */
  getModulesByCategory(category: string): Observable<DashboardModule[]> {
    return this.activeModules$.pipe(
      tap(modules => {
        const filtered = modules.filter(m => m.category === category);
        console.log(`📊 Modules in category '${category}': ${filtered.length}`);
      })
    );
  }

  /**
   * Reorder modules
   */
  reorderModules(moduleIds: string[]): void {
    const config = this.configSubject.value;
    if (config) {
      config.enabledModuleIds = moduleIds;
      config.updatedAt = new Date().toISOString();
      this.configSubject.next(config);
      this.updateActiveModules(config);
      console.log(`✅ Modules reordered`);
    }
  }

  /**
   * Get module by ID
   */
  getModule(moduleId: string): DashboardModule | null {
    const modules = this.availableModulesSubject.value;
    return modules.find(m => m.id === moduleId) || null;
  }

  /**
   * Export dashboard configuration
   */
  exportConfig(farmId: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/farms/${farmId}/config/export`, { responseType: 'blob' }).pipe(
      catchError(err => throwError(() => new Error(`Failed to export config: ${err.message}`)))
    );
  }
}
