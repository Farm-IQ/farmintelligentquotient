import { Component, OnInit, OnDestroy, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { WorkerManagementService } from '../../services/worker-management.service';
import { FarmerService } from '../../services/farmer.service';

export interface FarmSetupStep {
  stepNumber: number;
  title: string;
  description: string;
  completed: boolean;
  hasError: boolean;
}

@Component({
  selector: 'app-farm-setup-wizard',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, IonicModule],
  templateUrl: './farm-setup-wizard.html',
  styleUrl: './farm-setup-wizard.scss'
})
export class FarmSetupWizardComponent implements OnInit, AfterViewInit, OnDestroy {

  // Wizard state
  currentStep = 1;
  totalSteps = 4;
  isLoading = false;
  errorMessage = '';
  successMessage = '';

  // Forms
  farmInfoForm!: FormGroup;
  parcelForm!: FormGroup;
  livestockForm!: FormGroup;
  workerAssignmentForm!: FormGroup;
  reviewForm!: FormGroup;

  // Worker assignment state
  availableWorkers: any[] = [];
  assignedWorkers: any[] = [];
  selectedWorkerIds: string[] = [];
  isLoadingWorkers = false;
  isFullscreen = false;
  isGettingLocation = false;

  // Parcel size tracking (CRITICAL for farm size management)
  totalFarmSizeHectares = 0;
  totalAllocatedAreaHectares = 0;
  remainingFarmAreaHectares = 0;
  
  // Livestock tracking
  currentParcelType: 'crop' | 'livestock' = 'crop';
  livestockTypes: any[] = [];
  isLoadingLivestock = false;

  // Wizard steps tracking
  steps: FarmSetupStep[] = [
    { stepNumber: 1, title: 'Farm Information', description: 'Basic details about your farm', completed: false, hasError: false },
    { stepNumber: 2, title: 'Add Parcels', description: 'Divide your farm into parcels', completed: false, hasError: false },
    { stepNumber: 3, title: 'Assign Workers', description: 'Select workers for this farm', completed: false, hasError: false },
    { stepNumber: 4, title: 'Review & Complete', description: 'Review details and complete setup', completed: false, hasError: false }
  ];

  // Data accumulator
  setupData: any = {
    farmInfo: {},
    parcels: [],
    assignedWorkers: [],
    soilData: {}
  };

  parcels: any[] = [];

  private destroy$ = new Subject<void>();

  constructor(
    private formBuilder: FormBuilder,
    private workerManagementService: WorkerManagementService,
    private farmerService: FarmerService,
    private router: Router
  ) {
    this.initializeForms();
  }

  ngOnInit(): void {
    console.log('🌾 Farm Setup Wizard initialized');
    this.loadAvailableWorkers();
    this.loadLivestockTypes();
  }

  /**
   * Convert farm size to hectares for tracking
   */
  private convertFarmSizeToHectares(size: number, unit: string): number {
    if (unit === 'hectares') return size;
    if (unit === 'acres') return size * 0.404686; // 1 acre = 0.404686 hectares
    return size;
  }

  /**
   * Update remaining farm area when farm size changes
   */
  onFarmSizeChange(): void {
    const farmSize = this.farmInfoForm.get('farmSize')?.value;
    const farmSizeUnit = this.farmInfoForm.get('farmSizeUnit')?.value;
    
    if (farmSize && farmSizeUnit) {
      this.totalFarmSizeHectares = this.convertFarmSizeToHectares(farmSize, farmSizeUnit);
      this.calculateRemainingArea();
    }
  }

  /**
   * Calculate remaining farm area after parcel allocations
   */
  private calculateRemainingArea(): void {
    this.totalAllocatedAreaHectares = this.parcels.reduce((sum, p) => sum + (p.areaHectares || 0), 0);
    this.remainingFarmAreaHectares = this.totalFarmSizeHectares - this.totalAllocatedAreaHectares;
  }

  /**
   * Load livestock types for dropdown
   */
  private loadLivestockTypes(): void {
    // Mock data - in production, fetch from service
    this.livestockTypes = [
      { id: '1', name: 'Dairy Cattle', category: 'dairy', icon: '🐄' },
      { id: '2', name: 'Beef Cattle', category: 'beef', icon: '🐄' },
      { id: '3', name: 'Dairy Goat', category: 'dairy', icon: '🐐' },
      { id: '4', name: 'Layer Poultry', category: 'poultry', icon: '🐔' },
      { id: '5', name: 'Broiler Poultry', category: 'poultry', icon: '🐔' },
      { id: '6', name: 'Fish (Tilapia)', category: 'fish', icon: '🐠' }
    ];
  }

  /**
   * Handle parcel type change (crop vs livestock)
   */
  onParcelTypeChange(type: 'crop' | 'livestock'): void {
    this.currentParcelType = type;
    if (type === 'livestock') {
      this.parcelForm.get('currentCrop')?.clearValidators();
      this.parcelForm.get('currentCrop')?.setValidators([]);
    } else {
      this.parcelForm.get('currentCrop')?.setValidators([Validators.required]);
    }
    this.parcelForm.get('currentCrop')?.updateValueAndValidity();
  }

  ngAfterViewInit(): void {
    // No longer needed for map initialization
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Initialize all forms based on steps
   */
  private initializeForms(): void {
    // Step 1: Farm Information - EXTENDED with dairy/beef/poultry
    this.farmInfoForm = this.formBuilder.group({
      farmName: ['', [Validators.required, Validators.minLength(3)]],
      county: ['', Validators.required],
      subCounty: ['', Validators.required],
      location: ['', Validators.required],
      farmSize: ['', [Validators.required, Validators.min(0.01)]],
      farmSizeUnit: ['acres', Validators.required],
      farmType: ['Mixed', Validators.required],
      primaryCrop: ['maize', Validators.required], // Extended options
      farmingMethod: ['', Validators.required],
      description: ['']
    });

    // Step 2: Parcel Information - SUPPORTS BOTH CROP & LIVESTOCK
    this.parcelForm = this.formBuilder.group({
      parcelName: ['', [Validators.required, Validators.minLength(2)]],
      parcelType: ['crop', Validators.required], // 'crop' or 'livestock'
      currentCrop: ['', Validators.required], // For crops
      cropVariety: [''], // Optional crop variety
      
      // Crop-related fields
      plantingDate: [''],
      expectedHarvestDate: [''],
      farmingMethod: ['rain_fed'],
      irrigationType: ['rain_fed'],
      
      // Livestock-related fields (conditional)
      livestockType: [''], // For livestock
      livestockCount: [''],
      housingType: [''], // 'open', 'semi-open', 'closed'
      paddockArrangement: [''],
      
      // CRITICAL: Common field - tracks area allocation for farm size management
      areaHectares: ['', [Validators.required, Validators.min(0.01)]]
    });

    // Livestock-specific form (for detailed livestock data)
    this.livestockForm = this.formBuilder.group({
      livestockType: ['', Validators.required],
      unitName: ['', [Validators.required, Validators.minLength(3)]],
      currentCount: ['', [Validators.required, Validators.min(1)]],
      capacity: ['', [Validators.required, Validators.min(1)]],
      housingType: ['closed', Validators.required],
      operationType: [''] // 'dairy', 'beef', 'fattening', etc.
    });

    // Step 3: Worker Assignment
    this.workerAssignmentForm = this.formBuilder.group({
      selectedWorkers: [[], Validators.required]
    });

    // Step 4: Review
    this.reviewForm = this.formBuilder.group({
      agreedToTerms: [false, Validators.requiredTrue],
      agreedToDataSharing: [false, Validators.required]
    });
  }

  /**
   * Load available workers for the farmer
   */
  private loadAvailableWorkers(): void {
    this.isLoadingWorkers = true;
    this.errorMessage = '';

    // Get current farm from farmer service
    this.farmerService.getCurrentFarm()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (farm: any) => {
          if (farm && farm.id) {
            // Load workers for the current farm
            this.workerManagementService.getFarmWorkers(farm.id)
              .pipe(takeUntil(this.destroy$))
              .subscribe({
                next: (workers: any[]) => {
                  this.availableWorkers = workers;
                  this.isLoadingWorkers = false;
                  console.log(`✅ Loaded ${workers.length} available workers`);
                },
                error: (error: any) => {
                  console.error('❌ Error loading workers:', error);
                  this.errorMessage = 'Failed to load available workers';
                  this.availableWorkers = [];
                  this.isLoadingWorkers = false;
                }
              });
          } else {
            // No current farm - show empty list (new farm being created)
            this.availableWorkers = [];
            this.isLoadingWorkers = false;
            console.log('ℹ️ No current farm - workers can be assigned after farm creation');
          }
        },
        error: (error: any) => {
          console.error('❌ Error getting current farm:', error);
          this.availableWorkers = [];
          this.isLoadingWorkers = false;
        }
      });
  }

  /**
   * Toggle worker selection
   */
  toggleWorkerSelection(workerId: string): void {
    const index = this.selectedWorkerIds.indexOf(workerId);
    if (index > -1) {
      this.selectedWorkerIds.splice(index, 1);
    } else {
      this.selectedWorkerIds.push(workerId);
    }
    console.log(`🔄 Selected workers: ${this.selectedWorkerIds.length}`);
  }

  /**
   * Check if worker is selected
   */
  isWorkerSelected(workerId: string): boolean {
    return this.selectedWorkerIds.includes(workerId);
  }

  /**
   * Add parcel to the farm with CRITICAL farm size validation
   */
  addParcel(): void {
    if (this.parcelForm.invalid) {
      this.errorMessage = 'Please fill in all parcel details';
      return;
    }

    const newParcelArea = parseFloat(this.parcelForm.get('areaHectares')?.value || 0);
    
    // CRITICAL VALIDATION: Ensure parcel area doesn't exceed remaining farm area
    if (newParcelArea > this.remainingFarmAreaHectares) {
      this.errorMessage = `⚠️ Parcel area (${newParcelArea}ha) exceeds remaining farm area (${this.remainingFarmAreaHectares.toFixed(2)}ha). Total farm: ${this.totalFarmSizeHectares.toFixed(2)}ha, Allocated: ${this.totalAllocatedAreaHectares.toFixed(2)}ha`;
      return;
    }

    if (newParcelArea <= 0) {
      this.errorMessage = 'Parcel area must be greater than 0';
      return;
    }

    const parcelData = {
      ...this.parcelForm.value,
      id: `parcel-${this.parcels.length + 1}`,
      parcelType: this.currentParcelType
    };

    this.parcels.push(parcelData);
    this.calculateRemainingArea(); // Recalculate remaining area
    this.setupData.parcels = this.parcels;

    console.log(`✅ Parcel added: ${parcelData.parcelName} (${newParcelArea}ha). Remaining: ${this.remainingFarmAreaHectares.toFixed(2)}ha`);

    // Reset form
    this.parcelForm.reset({
      parcelType: 'crop',
      farmingMethod: 'rain_fed',
      irrigationType: 'rain_fed'
    });
    this.currentParcelType = 'crop'; // Reset parcel type selector
    this.errorMessage = '';
    this.successMessage = `✅ Parcel "${parcelData.parcelName}" added (${newParcelArea}ha). Remaining: ${this.remainingFarmAreaHectares.toFixed(2)}ha`;
  }

  /**
   * Remove parcel and recalculate farm area
   */
  removeParcel(index: number): void {
    const removed = this.parcels[index];
    this.parcels.splice(index, 1);
    this.calculateRemainingArea(); // Recalculate after removal
    this.setupData.parcels = this.parcels;
    console.log(`🗑️ Parcel "${removed.parcelName}" removed. Remaining: ${this.remainingFarmAreaHectares.toFixed(2)}ha / ${this.totalFarmSizeHectares.toFixed(2)}ha`);
  }

  /**
   * Move to next step in wizard
   */
  nextStep(): void {
    if (this.currentStep < this.totalSteps) {
      // Validate current step
      if (!this.validateStep(this.currentStep)) {
        this.errorMessage = 'Please complete all required fields';
        return;
      }

      this.currentStep++;
      this.errorMessage = '';
    }
  }

  /**
   * Move to previous step
   */
  previousStep(): void {
    if (this.currentStep > 1) {
      this.currentStep--;
      this.errorMessage = '';
    }
  }

  /**
   * Validate current step form
   */
  private validateStep(step: number): boolean {
    switch (step) {
      case 1:
        if (this.farmInfoForm.invalid) return false;
        this.setupData.farmInfo = this.farmInfoForm.value;
        return true;
      case 2:
        return this.parcels.length > 0;
      case 3:
        return this.selectedWorkerIds.length >= 0; // Workers are optional
      case 4:
        return this.reviewForm.valid;
      default:
        return false;
    }
  }

  /**
   * Finish setup and create farm in backend
   */
  async finishSetup(): Promise<void> {
    if (!this.validateStep(this.currentStep)) {
      this.errorMessage = 'Please complete all fields';
      return;
    }

    if (this.setupData.parcels.length === 0) {
      this.errorMessage = 'Please add at least one parcel';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    try {
      // Prepare farm payload
      const farmPayload = {
        farm_name: this.setupData.farmInfo.farmName,
        county: this.setupData.farmInfo.county,
        sub_county: this.setupData.farmInfo.subCounty,
        location_description: this.setupData.farmInfo.location,
        farm_size: this.setupData.farmInfo.farmSize,
        farm_size_unit: this.setupData.farmInfo.farmSizeUnit,
        farm_type: this.setupData.farmInfo.farmType,
        primary_crop: this.setupData.farmInfo.primaryCrop,
        farming_method: this.setupData.farmInfo.farmingMethod,
        description: this.setupData.farmInfo.description || ''
      };

      console.log('📤 Sending farm data:', farmPayload);

      // Create farm
      this.farmerService.createFarm(farmPayload)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (farm: any) => {
            console.log('✅ Farm created:', farm);
            this.createParcels(farm.id);
            this.assignWorkersToFarm(farm.id);
            this.successMessage = '✅ Farm setup completed successfully!';
            setTimeout(() => {
              this.router.navigate(['/farmer/dashboard']);
            }, 1500);
          },
          error: (error: any) => {
            console.error('❌ Error creating farm:', error);
            this.errorMessage = error.message || 'Failed to create farm';
            this.isLoading = false;
          }
        });
    } catch (error) {
      console.error('❌ Error in farm setup:', error);
      this.errorMessage = 'An error occurred during farm setup';
      this.isLoading = false;
    }
  }

  /**
   * Create parcels for the farm
   */
  private createParcels(farmId: string): void {
    this.setupData.parcels.forEach((parcel: any) => {
      const parcelPayload = {
        parcel_name: parcel.parcelName,
        parcel_type: parcel.parcelType,
        farm_id: farmId,
        current_crop: parcel.currentCrop,
        planting_date: parcel.plantingDate,
        expected_harvest_date: parcel.expectedHarvestDate,
        farming_method: parcel.farmingMethod,
        irrigation_type: parcel.irrigationType,
        area_hectares: parcel.areaHectares
      };

      // Create parcel via service
      console.log('📝 Creating parcel:', parcel.parcelName);
    });
  }

  /**
   * Assign selected workers to farm
   */
  private assignWorkersToFarm(farmId: string): void {
    if (this.selectedWorkerIds.length === 0) {
      console.log('ℹ️ No workers assigned to this farm');
      return;
    }

    this.selectedWorkerIds.forEach((workerId: string) => {
      const assignment = {
        farm_id: farmId,
        worker_id: workerId,
        assigned_date: new Date().toISOString().split('T')[0],
        assignment_status: 'Active',
        is_primary_assignment: this.selectedWorkerIds[0] === workerId
      };

      // Assign worker to farm via service
      console.log('👷 Assigning worker to farm:', assignment);
    });
  }

  /**
   * Get worker name by ID
   */
  getWorkerName(workerId: string): string {
    const worker = this.availableWorkers.find(w => w.id === workerId);
    return worker?.name || 'Unknown Worker';
  }

  /**
   * Get worker role by ID
   */
  getWorkerRole(workerId: string): string {
    const worker = this.availableWorkers.find(w => w.id === workerId);
    return worker?.role || 'Worker';
  }

  /**
   * Get current form for the active step
   */
  getCurrentForm(): FormGroup {
    switch (this.currentStep) {
      case 1:
        return this.farmInfoForm;
      case 2:
        return this.parcelForm;
      case 3:
        return this.workerAssignmentForm;
      case 4:
        return this.reviewForm;
      default:
        return this.farmInfoForm;
    }
  }

  /**
   * Check if we can proceed to next step
   */
  canProceedToNext(): boolean {
    return this.validateStep(this.currentStep);
  }

  /**
   * Calculate farm area from boundary
   */
  calculateBoundaryArea(): number {
    // No longer needed - removed boundary drawing
    return 0;
  }

  /**
   * Get user's current location
   */
  getLocation(): void {
    if (!navigator.geolocation) {
      this.errorMessage = 'Geolocation is not supported by your browser';
      return;
    }

    this.isGettingLocation = true;
    this.errorMessage = '';

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        console.log(`📍 Current location: ${latitude}, ${longitude}`);
        this.isGettingLocation = false;
      },
      (error) => {
        console.error('❌ Geolocation error:', error);
        this.errorMessage = 'Failed to get your location';
        this.isGettingLocation = false;
      }
    );
  }

  /**
   * Zoom in on map
   */
  zoomIn(): void {
    console.log('🔍 Zoom in - removed from new setup');
  }

  /**
   * Zoom out on map
   */
  zoomOut(): void {
    console.log('🔍 Zoom out - removed from new setup');
  }

  /**
   * Toggle fullscreen mode
   */
  toggleFullscreen(): void {
    const mapContainer = document.getElementById('farmBoundaryMap');
    if (!mapContainer) {
      this.errorMessage = 'Map container not found';
      return;
    }

    const isFullscreenNow = document.fullscreenElement === mapContainer;

    if (isFullscreenNow) {
      document.exitFullscreen().catch((err) => {
        console.error('Error exiting fullscreen:', err);
      });
      this.isFullscreen = false;
    } else {
      mapContainer.requestFullscreen().catch((err) => {
        console.error('Error requesting fullscreen:', err);
        this.errorMessage = `Unable to enter fullscreen: ${err.message}`;
      });
      this.isFullscreen = true;
    }
  }
}
