/**
 * LIVESTOCK AND AGRICULTURAL OPERATIONS MODELS
 * Comprehensive models for crop and livestock farming with integrated financial tracking
 */

// Farm interface - for farming operations
export interface Farm {
  id: string;
  user_id: string;
  name: string;
  county: string;
  location: string;
  latitude: number;
  longitude: number;
  size_acres: number;
  soil_type: string;
  created_at: string;
  updated_at: string;
}

// Farm Parcel - portion of a farm allocated to specific crops/livestock
export interface FarmParcel {
  id: string;
  farm_id: string;
  parcel_name: string;
  area_acres: number;
  crop_or_livestock: 'crop' | 'livestock';
  status: 'active' | 'fallow' | 'preparation';
  soil_type: string;
  created_at: string;
  updated_at: string;
}

/**
 * Enumeration of farming operation types
 */
export enum FarmingOperationType {
  CROP_PRODUCTION = 'crop_production',
  LIVESTOCK_DAIRY = 'livestock_dairy',
  LIVESTOCK_BEEF = 'livestock_beef',
  LIVESTOCK_POULTRY = 'livestock_poultry',
  LIVESTOCK_AQUACULTURE = 'livestock_aquaculture',
  MIXED_CROP_LIVESTOCK = 'mixed_crop_livestock'
}

/**
 * Enumeration of livestock categories
 */
export enum LivestockCategory {
  DAIRY = 'dairy',
  BEEF = 'beef',
  POULTRY = 'poultry',
  GOAT = 'goat',
  SHEEP = 'sheep',
  FISH = 'fish',
  PIG = 'pig'
}

/**
 * Enumeration of primary crops including poultry (specialized operation)
 */
export enum PrimaryCropType {
  MAIZE = 'maize',
  WHEAT = 'wheat',
  RICE = 'rice',
  COFFEE = 'coffee',
  TEA = 'tea',
  BANANA = 'banana',
  TOMATO = 'tomato',
  POTATO = 'potato',
  BEANS = 'beans',
  PEAS = 'peas',
  CABBAGE = 'cabbage',
  KALE = 'kale',
  SUGARCANE = 'sugarcane',
  COTTON = 'cotton',
  SUNFLOWER = 'sunflower',
  AVOCADO = 'avocado',
  MANGO = 'mango',
  CITRUS = 'citrus',
  POULTRY = 'poultry', // Layer or broiler farming
  DAIRY = 'dairy',
  BEEF = 'beef'
}

/**
 * Livestock Type Definition
 */
export interface LivestockType {
  id: string;
  name: string;
  category: LivestockCategory;
  scientificName?: string;
  averageWeightKg?: number;
  gestationPeriodDays?: number;
  milkProductionPerDayLiters?: number;
  eggProductionPerYear?: number;
  averageLifespanYears?: number;
  housingRequirementSqmPerUnit?: number;
  feedRequirementKgPerDay?: number;
  waterRequirementLitersPerDay?: number;
  description?: string;
  iconEmoji?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Farm Livestock Unit - represents a group of livestock managed together
 */
export interface FarmLivestockUnit {
  id: string;
  farmId: string;
  livestockTypeId: string;
  livestockType?: LivestockType; // Populated for detail views
  unitName: string; // e.g., "Dairy Unit A", "Broiler House 1"
  locationDescription?: string;
  currentCount: number;
  capacityCount: number;
  
  // Housing and infrastructure
  housingType: 'open' | 'semi-open' | 'closed' | 'pond';
  housingAreaSqm?: number;
  
  // Operational details
  operationType?: 'dairy' | 'beef' | 'breeding' | 'fattening' | 'layers' | 'broilers';
  status: 'active' | 'inactive' | 'maintenance';
  establishedDate?: string;
  
  // Financial
  purchaseCostPerUnit?: number;
  totalInvestmentCost?: number;
  depreciationRatePercent?: number;
  
  createdAt: string;
  updatedAt: string;
}

/**
 * Livestock Health Record - vaccination, medication, disease tracking
 */
export interface LivestockHealthRecord {
  id: string;
  livestockUnitId: string;
  recordDate: string;
  recordType: 'vaccination' | 'medication' | 'treatment' | 'disease' | 'check-up';
  description: string;
  affectedCount?: number;
  veterinarianName?: string;
  medicationName?: string;
  cost?: number;
  notes?: string;
  photoUrl?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Livestock Production Record - milk, eggs, offspring, weight gain
 */
export interface LivestockProductionRecord {
  id: string;
  livestockUnitId: string;
  recordDate: string;
  productionType: 'milk_production' | 'egg_production' | 'weight_gain' | 'breeding';
  quantityProduced: number;
  unit: 'liters' | 'pieces' | 'kg' | 'dozen';
  qualityGrade?: 'A' | 'B' | 'C' | 'large' | 'medium' | 'small';
  revenueGenerated?: number;
  costInput?: number; // feed, medication costs for this period
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Farm Operations - tracks different operations (crop vs livestock)
 */
export interface FarmOperation {
  id: string;
  farmId: string;
  operationName: string;
  operationType: FarmingOperationType;
  primaryCommodity: string; // 'coffee', 'maize', 'dairy', 'beef', 'poultry'
  startDate: string;
  endDate?: string;
  status: 'active' | 'completed' | 'paused';
  
  // Resource allocation
  allocatedLandHectares?: number;
  allocatedBudget?: number;
  
  createdAt: string;
  updatedAt: string;
}

/**
 * Inventory Category Reference Data
 */
export interface InventoryCategory {
  id: string;
  name: string; // 'Animal Feed', 'Seeds', 'Fertilizer', 'Equipment', etc.
  description?: string;
  iconEmoji?: string;
}

/**
 * Farm Inventory - Stock management per item
 */
export interface FarmInventory {
  id: string;
  farmId: string;
  categoryId: string;
  itemName: string;
  description?: string;
  currentQuantity: number;
  unit: string; // 'kg', 'liters', 'pieces', 'bags'
  reorderLevel?: number;
  reorderQuantity?: number;
  unitCost?: number;
  supplierName?: string;
  supplierContact?: string;
  lastRestockDate?: string;
  expiryDate?: string;
  locationInFarm?: string;
  status: 'in-stock' | 'low-stock' | 'out-of-stock' | 'expired';
  createdAt: string;
  updatedAt: string;
}

/**
 * Inventory Transaction - audit trail for stock movements
 */
export interface InventoryTransaction {
  id: string;
  inventoryId: string;
  farmId: string;
  transactionType: 'purchase' | 'use' | 'sale' | 'damage' | 'adjustment';
  quantityChanged: number;
  transactionDate: string;
  referenceId?: string; // links to parcel, livestock unit, or sales
  referenceType?: 'parcel' | 'livestock_unit' | 'sale' | 'other';
  costTransaction?: number;
  recordedBy?: string; // user_id
  notes?: string;
  createdAt: string;
}

/**
 * Farm Cost Tracking
 */
export interface FarmCost {
  id: string;
  farmId: string;
  operationId?: string;
  costCategory: 'land_preparation' | 'seeds' | 'fertilizer' | 'labor' | 'equipment' | 'feed' | 'medication' | 'housing';
  costType: 'fixed' | 'variable';
  description?: string;
  amount: number;
  costDate: string;
  relatedInventoryId?: string;
  recordedBy?: string; // user_id
  invoiceNumber?: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Farm Revenue Tracking
 */
export interface FarmRevenue {
  id: string;
  farmId: string;
  operationId?: string;
  revenueType: 'crop_sale' | 'livestock_sale' | 'dairy_sale' | 'egg_sale' | 'other';
  commoditySold: string;
  quantitySold: number;
  unit: string;
  pricePerUnit: number;
  totalRevenue: number;
  saleDate: string;
  buyerName?: string;
  buyerType?: 'individual' | 'wholesaler' | 'cooperative' | 'processor' | 'retailer';
  paymentMethod?: 'cash' | 'mobile_money' | 'bank_transfer' | 'credit';
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Financial Summary - aggregated period performance
 */
export interface FarmFinancialSummary {
  id: string;
  farmId: string;
  operationId?: string;
  periodStartDate: string;
  periodEndDate: string;
  periodType: 'cycle' | 'quarter' | 'year';
  
  // Calculated metrics
  totalCosts: number;
  totalRevenue: number;
  grossProfit: number;
  roiPercentage?: number;
  breakEvenUnits?: number;
  
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Coffee-Specific Operations
 */
export interface CoffeeOperation {
  id: string;
  farmId: string;
  operationId: string;
  parcelId?: string;
  
  // Coffee farm specifics
  coffeeVariety: 'Arabica' | 'Robusta' | 'Typica' | 'Other';
  plantingDensityPerHectare: number;
  shadeTreeType?: string; // 'Grevillea', 'Banana', 'Calliandra'
  shadeTreeCoveragePercent?: number;
  
  // Paddock arrangement
  paddockCount: number;
  paddockRotationYears: number;
  currentPaddockInRotation: number;
  
  // Productivity
  expectedCherryYieldKgPerHectare?: number;
  actualCherryYieldKgPerHectare?: number;
  processingMethod: 'washed' | 'natural' | 'honey';
  moistureContentPercent?: number;
  
  // Quality grading
  defectCountPer100g?: number;
  screenSizeMm?: string;
  grade?: 'specialty' | 'premium' | 'commercial';
  
  // Maintenance dates
  lastPruningDate?: string;
  lastFertilizerApplicationDate?: string;
  
  createdAt: string;
  updatedAt: string;
}

/**
 * Dairy-Specific Operations
 */
export interface DairyOperation {
  id: string;
  farmId: string;
  operationId: string;
  livestockUnitId: string;
  
  // Cattle management
  totalMilkingAnimals: number;
  averageMilkProductionLitersPerDay: number;
  milkQualityButterfatPercent?: number;
  milkQualityProteinPercent?: number;
  somaticCellCountThousandPerMl?: number;
  
  // Breeding
  lastBreedingDate?: string;
  expectedCalvingDate?: string;
  calvesOnThisYear?: number;
  calfMortalityPercent?: number;
  
  // Paddock arrangement
  paddockCount: number;
  grazingRotationDays: number;
  currentPaddock: number;
  paddockSizeHectares?: number;
  
  // Infrastructure
  milkingSystemType: 'manual' | 'machine';
  milkStorageCapacityLiters?: number;
  milkCoolingSystem?: string;
  
  // Certification
  isCertifiedOrganic?: boolean;
  certificationNumber?: string;
  
  createdAt: string;
  updatedAt: string;
}

/**
 * Extended Farm Parcel for Crop-Specific Data
 */
export interface ExtendedFarmParcel extends FarmParcel {
  // Newly added parcel size tracking
  allocatedAreaHectares?: number; // Allocated from farm size
  remainingFarmArea?: number; // Calculated: total farm size - sum of all parcel areas
  
  // Crop-specific fields (for future extensibility)
  isCropParcel?: boolean;
  isLivestockParcel?: boolean; // if true, references livestock_unit_id
  
  // Livestock reference (if applicable)
  livestockUnitId?: string;
  livestockCount?: number;
  
  createdAt: string;
  updatedAt: string;
}

/**
 * Dashboard Module Definition
 */
export interface DashboardModule {
  id: string;
  title: string;
  name?: string; // Alias for readability
  description: string;
  componentName: string;
  operationType?: FarmingOperationType;
  commodityType?: PrimaryCropType | LivestockCategory;
  displayOrder: number;
  position?: number; // Alias for displayOrder
  isRequired: boolean;
  enabled?: boolean; // To track enabled/disabled state
  icon: string;
  category?: string; // e.g., 'general', 'crop', 'livestock', 'financial'
  requiredOperations?: string[];
  requiredCrops?: string[];
  component?: string; // Component to render
}

/**
 * Dashboard Configuration per Farm
 */
export interface FarmDashboardConfig {
  id?: string; // Dashboard config ID
  farmId: string;
  operationId?: string;
  selectedModules?: DashboardModule[];
  enabledModuleIds?: string[]; // List of enabled module IDs
  moduleSettings?: Record<string, any>;
  customization?: Record<string, any>;
  lastUpdated?: string;
  updatedAt?: string;
  createdAt?: string;
}

/**
 * Farm Activity - Tracks daily farm operations and activities
 */
export interface FarmActivity {
  id: string;
  farmId: string;
  parcelId?: string;
  activityType: 'planting' | 'weeding' | 'fertilizing' | 'harvesting' | 'irrigation' | 'inspection' | 'maintenance';
  description: string;
  activityDate: string;
  completedBy?: string;
  duration_hours?: number;
  inputs_used?: Record<string, any>;
  labor_cost?: number;
  createdAt: string;
  updatedAt: string;
}

/**
 * Soil Sample - Soil testing and analysis results
 */
export interface SoilSample {
  id: string;
  farmId: string;
  parcelId: string;
  sampleDate: string;
  gpsCoordinate?: { latitude: number; longitude: number };
  depth_cm?: number;
  soil_type?: string;
  ph?: number;
  nitrogen_ppm?: number;
  phosphorus_ppm?: number;
  potassium_ppm?: number;
  organic_matter_percent?: number;
  texture?: string;
  recommendation?: string;
  lab_report_url?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Farmer Assessment - Periodic farmer capability and knowledge assessment
 */
export interface FarmerAssessment {
  id: string;
  farmerId: string;
  farmId: string;
  assessmentDate: string;
  assessmentType: 'knowledge' | 'capability' | 'business' | 'technology_adoption';
  score: number;
  max_score: number;
  percentage: number;
  category?: string;
  details?: Record<string, any>;
  assessor_id?: string;
  recommendations?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Farmer Statistics - Aggregated metrics and KPIs for farmer
 */
export interface FarmerStatistics {
  id: string;
  farmerId: string;
  farmId: string;
  statisticsPeriod: 'monthly' | 'quarterly' | 'yearly';
  periodStartDate: string;
  periodEndDate: string;
  total_activities?: number;
  total_harvest_kg?: number;
  total_revenue?: number;
  total_expenses?: number;
  average_yield_kg_per_hectare?: number;
  soil_health_score?: number;
  technology_adoption_rate?: number;
  custom_metrics?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}
