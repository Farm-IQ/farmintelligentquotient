import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { FarmerService } from '../../services/farmer.service';
import { LivestockManagementService } from '../../services/livestock-management.service';
import { InventoryManagementService } from '../../services/inventory-management.service';
import { FarmFinancialService } from '../../services/farm-financial.service';
import { FarmDashboardConfigService } from '../../services/farm-dashboard-config.service';
import { environment } from '../../../../../environments/environment';
import { Subject } from 'rxjs';
import { takeUntil, finalize } from 'rxjs/operators';
import maplibregl from 'maplibre-gl';

// Import actual models
import { Farm } from '../../models/livestock-operations.models';
import { FarmOperation, FarmLivestockUnit, FarmInventory } from '../../models/livestock-operations.models';

interface Analytics {
  yieldMetrics: { current_season: number; last_season: number; average: number };
  weatherImpact: number;
  soilHealth: number;
  waterUsage: number;
  recommendations: string[];
}

interface Recommendation {
  title: string;
  description: string;
  impact: string;
}

interface FinancialSummary {
  totalCosts: number;
  totalRevenue: number;
  grossProfit: number;
  roiPercentage: number;
}

@Component({
  selector: 'app-farmer-analytics',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule, IonicModule],
  templateUrl: './farmer-analytics.html',
  styleUrls: ['./farmer-analytics.scss']
})
export class FarmerAnalyticsComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('mapContainer') mapContainer!: ElementRef;

  Math = Math;
  
  // UI State
  loading = true;
  error: string | null = null;
  errorDetails: string = '';
  activeMenu = 'farm-overview';
  showCreateFarmModal = false;
  showCreateOperationModal = false;
  showAddLivestockModal = false;
  showAddInventoryModal = false;
  mapReady = false;
  showMap = true;
  mapProviderInfo: any = null;
  private map: maplibregl.Map | null = null;

  // Section Loading States
  loadingOperations = false;
  loadingLivestock = false;
  loadingInventory = false;
  loadingFinances = false;
  loadingAnalytics = false;

  // Error states per section
  operationsError: string | null = null;
  livestockError: string | null = null;
  inventoryError: string | null = null;
  financesError: string | null = null;
  analyticsError: string | null = null;

  // Retry attempts
  private retryAttempts: { [key: string]: number } = {};
  private maxRetries = 3;
  private retryDelay = 2000;

  // Data
  analytics: Analytics | null = null;
  farms: Farm[] = [];
  currentFarm: Farm | null = null;
  operations: FarmOperation[] = [];
  livestockUnits: FarmLivestockUnit[] = [];
  inventoryItems: FarmInventory[] = [];
  financialSummary: FinancialSummary = {
    totalCosts: 0,
    totalRevenue: 0,
    grossProfit: 0,
    roiPercentage: 0
  };

  // Forms
  createFarmForm!: FormGroup;
  createOperationForm!: FormGroup;
  addLivestockForm!: FormGroup;
  addInventoryForm!: FormGroup;

  // Metrics
  yieldGrowth = 0;
  recommendations: Recommendation[] = [
    {
      title: 'Optimize Soil pH',
      description: 'Current soil pH is slightly acidic. Consider adding lime.',
      impact: 'Potential 15% yield increase'
    },
    {
      title: 'Increase Irrigation',
      description: 'Water stress detected. Increase watering frequency.',
      impact: 'Reduce crop stress by 30%'
    },
    {
      title: 'Pest Management',
      description: 'Early signs of pest pressure detected.',
      impact: 'Prevent 20% potential loss'
    }
  ];

  private destroy$ = new Subject<void>();

  constructor(
    private formBuilder: FormBuilder,
    private farmerService: FarmerService,
    private livestockService: LivestockManagementService,
    private inventoryService: InventoryManagementService,
    private financialService: FarmFinancialService,
    private dashboardConfigService: FarmDashboardConfigService
  ) {
    this.initializeForms();
  }

  ngOnInit(): void {
    console.log('🌾 Loading Farmer Analytics Dashboard...');
    this.loadAllFarmData();
    setInterval(() => this.refreshAllData(), 10 * 60 * 1000);
  }

  ngAfterViewInit(): void {
    if (this.mapContainer && this.showMap) {
      setTimeout(() => this.initializeMap(), 500);
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    // GIS map cleanup removed (GIS implementation deferred)
  }

  // ========================================================================
  // INITIALIZATION & FORM SETUP
  // ========================================================================

  private initializeForms(): void {
    this.createFarmForm = this.formBuilder.group({
      farm_name: ['', [Validators.required, Validators.minLength(3)]],
      location: ['', Validators.required],
      area_hectares: ['', [Validators.required, Validators.min(0.1)]],
      farming_method: ['conventional', Validators.required],
      primary_crop: ['']
    });

    this.createOperationForm = this.formBuilder.group({
      operationName: ['', [Validators.required, Validators.minLength(2)]],
      operationType: ['crop_production', Validators.required],
      primaryCommodity: ['maize', Validators.required],
      allocatedBudget: [0, Validators.required],
      expectedYield: [0]
    });

    this.addLivestockForm = this.formBuilder.group({
      unitName: ['', [Validators.required, Validators.minLength(2)]],
      livestockTypeId: ['', Validators.required],
      currentCount: [1, [Validators.required, Validators.min(1)]],
      capacityCount: [10, [Validators.required, Validators.min(1)]],
      housingType: ['closed', Validators.required]
    });

    this.addInventoryForm = this.formBuilder.group({
      itemName: ['', [Validators.required, Validators.minLength(2)]],
      categoryId: ['', Validators.required],
      currentQuantity: [0, [Validators.required, Validators.min(0)]],
      unit: ['kg', Validators.required],
      reorderLevel: [5, Validators.required]
    });
  }

  // ========================================================================
  // DATA LOADING
  // ========================================================================

  loadAllFarmData(): void {
    this.loading = true;
    this.error = null;
    this.errorDetails = '';
    this.retryAttempts['farms'] = 0;

    this._loadFarmsWithRetry();
  }

  _loadFarmsWithRetry(): void {
    this.farmerService.getFarms()
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => this.loading = false)
      )
      .subscribe({
        next: (farms) => {
          this.farms = farms;
          if (farms.length > 0) {
            this.selectFarm(farms[0]);
          }
          this.error = null;
          console.log(`✅ Loaded ${farms.length} farms`);
        },
        error: (err: any) => {
          this.retryAttempts['farms'] = (this.retryAttempts['farms'] || 0) + 1;
          
          if (this.retryAttempts['farms'] < this.maxRetries) {
            console.warn(`⚠️ Failed to load farms. Retrying (${this.retryAttempts['farms']}/${this.maxRetries})...`);
            setTimeout(() => this._loadFarmsWithRetry(), this.retryDelay);
          } else {
            this.error = 'Failed to load farms';
            this.errorDetails = this._getErrorMessage(err);
            console.error('❌ Farm load error:', err);
          }
        }
      });
  }

  selectFarm(farm: Farm): void {
    this.currentFarm = farm;
    this.loadFarmData(farm.id);
  }

  loadFarmData(farmId: string): void {
    // Load operations
    this._loadOperations(farmId);

    // Load livestock
    this._loadLivestock(farmId);

    // Load inventory
    this._loadInventory(farmId);

    // Load finances
    this._loadFinances(farmId);

    // Load analytics
    this._loadAnalytics();
  }

  private _loadOperations(farmId: string, retryCount = 0): void {
    this.loadingOperations = true;
    this.operationsError = null;

    this.farmerService.getFarmOperationsOverview(farmId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (ops) => {
          this.operations = ops || [];
          this.loadingOperations = false;
          console.log(`✅ Loaded ${ops.length} operations`);
        },
        error: (err: any) => {
          this.loadingOperations = false;
          if (retryCount < this.maxRetries) {
            console.warn(`⚠️ Failed to load operations. Retrying (${retryCount + 1}/${this.maxRetries})...`);
            setTimeout(() => this._loadOperations(farmId, retryCount + 1), this.retryDelay);
          } else {
            this.operationsError = 'Unable to load operations: ' + this._getErrorMessage(err);
            console.error('❌ Failed to load operations:', err);
          }
        }
      });
  }

  private _loadLivestock(farmId: string, retryCount = 0): void {
    this.loadingLivestock = true;
    this.livestockError = null;

    this.livestockService.getFarmLivestockUnits(farmId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (units) => {
          this.livestockUnits = units || [];
          this.loadingLivestock = false;
          console.log(`✅ Loaded ${units.length} livestock units`);
        },
        error: (err: any) => {
          this.loadingLivestock = false;
          if (retryCount < this.maxRetries) {
            console.warn(`⚠️ Failed to load livestock. Retrying (${retryCount + 1}/${this.maxRetries})...`);
            setTimeout(() => this._loadLivestock(farmId, retryCount + 1), this.retryDelay);
          } else {
            this.livestockError = 'Unable to load livestock units: ' + this._getErrorMessage(err);
            console.error('❌ Failed to load livestock:', err);
          }
        }
      });
  }

  private _loadInventory(farmId: string, retryCount = 0): void {
    this.loadingInventory = true;
    this.inventoryError = null;

    this.inventoryService.getFarmInventory(farmId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (items) => {
          this.inventoryItems = items || [];
          this.loadingInventory = false;
          console.log(`✅ Loaded ${items.length} inventory items`);
        },
        error: (err: any) => {
          this.loadingInventory = false;
          if (retryCount < this.maxRetries) {
            console.warn(`⚠️ Failed to load inventory. Retrying (${retryCount + 1}/${this.maxRetries})...`);
            setTimeout(() => this._loadInventory(farmId, retryCount + 1), this.retryDelay);
          } else {
            this.inventoryError = 'Unable to load inventory: ' + this._getErrorMessage(err);
            console.error('❌ Failed to load inventory:', err);
          }
        }
      });
  }

  private _loadFinances(farmId: string, retryCount = 0): void {
    this.loadingFinances = true;
    this.financesError = null;

    this.financialService.getFarmFinancialSummary(farmId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (summary) => {
          this.financialSummary = {
            totalCosts: summary?.totalCosts || 0,
            totalRevenue: summary?.totalRevenue || 0,
            grossProfit: summary?.grossProfit || 0,
            roiPercentage: summary?.roiPercentage || 0
          };
          this.loadingFinances = false;
          console.log('✅ Loaded financial summary');
        },
        error: (err: any) => {
          this.loadingFinances = false;
          if (retryCount < this.maxRetries) {
            console.warn(`⚠️ Failed to load finances. Retrying (${retryCount + 1}/${this.maxRetries})...`);
            setTimeout(() => this._loadFinances(farmId, retryCount + 1), this.retryDelay);
          } else {
            this.financesError = 'Unable to load financial data: ' + this._getErrorMessage(err);
            console.error('❌ Failed to load finances:', err);
          }
        }
      });
  }

  private _loadAnalytics(retryCount = 0): void {
    this.loadingAnalytics = true;
    this.analyticsError = null;

    this.farmerService.getAnalytics()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (analytics) => {
          this.analytics = analytics;
          this.calculateYieldGrowth();
          this.loadingAnalytics = false;
          console.log('✅ Loaded analytics');
        },
        error: (err: any) => {
          this.loadingAnalytics = false;
          if (retryCount < this.maxRetries) {
            console.warn(`⚠️ Failed to load analytics. Retrying (${retryCount + 1}/${this.maxRetries})...`);
            setTimeout(() => this._loadAnalytics(retryCount + 1), this.retryDelay);
          } else {
            this.analyticsError = 'Unable to load analytics: ' + this._getErrorMessage(err);
            console.error('❌ Failed to load analytics:', err);
          }
        }
      });
  }

  refreshAllData(): void {
    if (this.currentFarm) {
      this.loadFarmData(this.currentFarm.id);
    }
  }

  // ========================================================================
  // FARM MANAGEMENT
  // ========================================================================

  createFarm(): void {
    if (this.createFarmForm.invalid) {
      console.warn('Invalid farm form');
      return;
    }

    const farmData = this.createFarmForm.value;
    this.farmerService.createFarm(farmData)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (farm) => {
          this.farms.push(farm);
          this.selectFarm(farm);
          this.showCreateFarmModal = false;
          this.createFarmForm.reset();
          console.log('✅ Farm created successfully');
        },
        error: (err) => {
          this.error = 'Failed to create farm';
          console.error('Create farm error:', err);
        }
      });
  }

  deleteFarm(farm: Farm): void {
          if (confirm(`Delete this farm? This action cannot be undone.`)) {
      this.farmerService.deleteFarm(farm.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            this.farms = this.farms.filter(f => f.id !== farm.id);
            if (this.currentFarm?.id === farm.id && this.farms.length > 0) {
              this.selectFarm(this.farms[0]);
            }
            console.log('✅ Farm deleted');
          },
          error: (err) => {
            this.error = 'Failed to delete farm';
            console.error('Delete farm error:', err);
          }
        });
    }
  }

  // ========================================================================
  // OPERATIONS MANAGEMENT
  // ========================================================================

  createOperation(): void {
    if (!this.currentFarm || this.createOperationForm.invalid) {
      console.warn('Invalid operation form or no farm selected');
      return;
    }

    const operationData = {
      ...this.createOperationForm.value,
      farm_id: this.currentFarm.id
    };

    this.financialService.createFarmOperation(this.currentFarm.id, operationData)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (operation) => {
          this.operations.push(operation);
          this.showCreateOperationModal = false;
          this.createOperationForm.reset();
          this.loadFarmData(this.currentFarm!.id);
          console.log('✅ Operation created successfully');
        },
        error: (err) => {
          this.error = 'Failed to create operation';
          console.error('Create operation error:', err);
        }
      });
  }

  deleteOperation(operation: FarmOperation): void {
    if (confirm(`Delete this operation?`)) {
      // Implementation would call service
      this.operations = this.operations.filter(o => o.id !== operation.id);
      console.log('✅ Operation deleted');
    }
  }

  // ========================================================================
  // LIVESTOCK MANAGEMENT
  // ========================================================================

  addLivestockUnit(): void {
    if (!this.currentFarm || this.addLivestockForm.invalid) {
      console.warn('Invalid livestock form or no farm selected');
      return;
    }

    const livestockData = {
      ...this.addLivestockForm.value,
      farm_id: this.currentFarm.id
    };

    this.livestockService.createLivestockUnit(this.currentFarm.id, livestockData)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (unit) => {
          this.livestockUnits.push(unit);
          this.showAddLivestockModal = false;
          this.addLivestockForm.reset();
          console.log('✅ Livestock unit added successfully');
        },
        error: (err) => {
          this.error = 'Failed to add livestock unit';
          console.error('Add livestock error:', err);
        }
      });
  }

  deleteLivestockUnit(unit: FarmLivestockUnit): void {
    if (confirm(`Delete this livestock unit?`)) {
      this.livestockService.deleteLivestockUnit(unit.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            this.livestockUnits = this.livestockUnits.filter(u => u.id !== unit.id);
            console.log('✅ Livestock unit deleted successfully');
          },
          error: (err) => {
            this.error = 'Failed to delete livestock unit';
            console.error('Delete livestock error:', err);
          }
        });
    }
  }

  // ========================================================================
  // INVENTORY MANAGEMENT
  // ========================================================================

  addInventoryItem(): void {
    if (!this.currentFarm || this.addInventoryForm.invalid) {
      console.warn('Invalid inventory form or no farm selected');
      return;
    }

    const inventoryData = {
      ...this.addInventoryForm.value,
      farm_id: this.currentFarm.id
    };

    this.inventoryService.createInventoryItem(this.currentFarm.id, inventoryData)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (item) => {
          this.inventoryItems.push(item);
          this.showAddInventoryModal = false;
          this.addInventoryForm.reset();
          console.log('✅ Inventory item added successfully');
        },
        error: (err) => {
          this.error = 'Failed to add inventory item';
          console.error('Add inventory error:', err);
        }
      });
  }

  deleteInventoryItem(item: FarmInventory): void {
    if (confirm(`Delete this inventory item?`)) {
      this.inventoryService.deleteInventoryItem(item.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            this.inventoryItems = this.inventoryItems.filter(i => i.id !== item.id);
            console.log('✅ Inventory item deleted');
          },
          error: (err) => {
            this.error = 'Failed to delete inventory item';
            console.error('Delete inventory error:', err);
          }
        });
    }
  }

  checkLowStockItems(): FarmInventory[] {
    return this.inventoryItems.filter(item => item.currentQuantity <= (item.reorderLevel || 0));
  }

  // ========================================================================
  // ANALYTICS CALCULATIONS
  // ========================================================================

  private calculateYieldGrowth(): void {
    if (!this.analytics?.yieldMetrics) {
      this.yieldGrowth = 0;
      return;
    }

    const { current_season, last_season } = this.analytics.yieldMetrics;
    this.yieldGrowth = last_season > 0 
      ? ((current_season - last_season) / last_season) * 100 
      : 0;
  }

  getTotalOperationsBudget(): number {
    return this.operations.reduce((sum, op) => sum + (op.allocatedBudget || 0), 0);
  }

  getTotalLivestock(): number {
    return this.livestockUnits.reduce((sum, unit) => sum + (unit.currentCount || 0), 0);
  }

  getInventoryValue(): number {
    return this.inventoryItems.length;
  }

  getLivestockProductionValue(): number {
    return this.livestockUnits.reduce((sum, unit) => 
      sum + ((unit.capacityCount || 0) * 500), 0); // Estimate
  }

  // ========================================================================
  // MAP FUNCTIONALITY
  // ========================================================================

  private initializeMap(): void {
    // GIS implementation deferred - map initialization disabled
    console.log('📍 Map initialization deferred (GIS implementation pending)');
    this.mapReady = false;
  }

  toggleMap(): void {
    this.showMap = !this.showMap;
    if (this.showMap && !this.mapReady) {
      setTimeout(() => this.initializeMap(), 500);
    }
  }

  // ========================================================================
  // MENU NAVIGATION
  // ========================================================================

  setActiveMenu(menu: string): void {
    this.activeMenu = menu;
    console.log(`📊 Active menu: ${menu}`);
  }

  getWeatherImpactClass(): string {
    if (!this.analytics) return '';
    const impact = this.analytics.weatherImpact.toString().toLowerCase();
    if (impact.includes('positive')) return 'impact-positive';
    if (impact.includes('negative')) return 'impact-negative';
    return 'impact-neutral';
  }

  getSoilHealthPercentage(): number {
    return this.analytics?.soilHealth || 0;
  }

  getOperationStatusColor(status: string): string {
    switch (status?.toLowerCase()) {
      case 'active': return 'success';
      case 'inactive': return 'medium';
      case 'planned': return 'warning';
      default: return 'primary';
    }
  }

  getInventoryStatusColor(status: string): string {
    switch (status?.toLowerCase()) {
      case 'in-stock': return 'success';
      case 'low-stock': return 'warning';
      case 'out-of-stock': return 'danger';
      case 'expired': return 'dark';
      default: return 'primary';
    }
  }

  // ========================================================================
  // ERROR HANDLING & UTILITY METHODS
  // ========================================================================

  private _getErrorMessage(error: any): string {
    if (!error) return 'An unknown error occurred';

    // Handle HTTP errors
    if (error.status) {
      switch (error.status) {
        case 0: return 'Network error. Check your internet connection.';
        case 400: return 'Invalid request. Please check your input.';
        case 401: return 'Unauthorized. Please log in again.';
        case 403: return 'You do not have permission to perform this action.';
        case 404: return 'Resource not found.';
        case 409: return 'This resource already exists.';
        case 500: return 'Server error. Please try again later.';
        case 503: return 'Service temporarily unavailable. Please try again later.';
        default: return `Error ${error.status}: ${error.statusText || 'Unknown error'}`;
      }
    }

    // Handle Supabase errors
    if (error.message) {
      if (error.message.includes('PKEY')) return 'Duplicate entry. This item already exists.';
      if (error.message.includes('FOREIGN KEY')) return 'Invalid reference. Related record not found.';
      if (error.message.includes('NOT NULL')) return 'Required field is missing.';
      return error.message;
    }

    return 'An unexpected error occurred. Please try again.';
  }

  clearError(): void {
    this.error = null;
    this.errorDetails = '';
  }

  retryLoadAllData(): void {
    this.loadAllFarmData();
  }
}
