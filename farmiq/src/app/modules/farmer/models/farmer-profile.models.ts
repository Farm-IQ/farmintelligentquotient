/**
 * FARMER PROFILE MODELS
 * 
 * Role-specific profile for farmers with GIS integration
 * Extends base UserProfile with farmer-specific information and spatial data
 */

import { UserProfile } from '../../auth/models/user-profile.models';

/**
 * Geographic coordinate pair
 */
export interface GpsCoordinate {
  latitude: number;
  longitude: number;
  accuracy_meters?: number;
  timestamp?: string;
}

/**
 * GeoJSON geometry for spatial data
 */
export interface GeoJsonGeometry {
  type: 'Point' | 'LineString' | 'Polygon' | 'MultiPoint' | 'MultiLineString' | 'MultiPolygon';
  coordinates: any;
}

/**
 * GeoJSON feature for farm boundaries and parcels
 */
export interface GeoJsonFeature {
  type: 'Feature';
  geometry: GeoJsonGeometry;
  properties: Record<string, any>;
}

/**
 * Farmer role-specific profile
 * Stored in farmer_profiles table in Supabase
 */
export interface FarmerProfile extends UserProfile {
  primary_role: 'farmer';
  
  // Farmer-specific fields
  farmer_profile: {
    id: string;
    user_id: string;
    
    // Farm information
    farm_name?: string;
    farm_size_acres?: number;
    farm_size_hectares?: number;
    
    // Location & Geographic data
    location?: string;
    county?: string;
    city?: string;
    gps_coordinates?: GpsCoordinate;
    gps_accuracy_meters?: number;
    
    // Farming details
    primary_crop?: string;
    secondary_crops?: string[];
    primary_livestock?: string;
    secondary_livestock?: string[];
    farming_method?: 'organic' | 'conventional' | 'mixed' | 'intensive';
    years_experience?: number;
    irrigation_type?: 'rain-fed' | 'drip' | 'flood' | 'sprinkler' | 'mixed';
    
    // Contact & preferences
    preferred_language?: string;
    notification_preferences?: Record<string, boolean>;
    
    // Documents & verification
    id_number?: string;
    id_type?: string;
    is_verified?: boolean;
    verified_at?: string;
    
    // Farmer scores (from FarmScore)
    farmscore?: number;
    last_assessment_date?: string;
    
    // Farm status
    is_active?: boolean;
    total_parcels?: number;
    total_activities?: number;
    
    // Timestamps
    created_at: string;
    updated_at: string;
  };
}

/**
 * Farmer profile update request
 */
export interface FarmerProfileUpdateRequest {
  farm_name?: string;
  farm_size_acres?: number;
  farm_size_hectares?: number;
  location?: string;
  county?: string;
  city?: string;
  primary_crop?: string;
  secondary_crops?: string[];
  years_experience?: number;
  farming_method?: 'organic' | 'conventional' | 'mixed' | 'intensive';
}

/**
 * Farm parcel/plot information (legacy farmer profile model)
 */
export interface FarmerProfileParcel {
  farmer_id: string;
  
  // Parcel information
  parcel_name: string;
  size_acres?: number;
  size_hectares?: number;
  
  // Location
  location_name?: string;
  gps_coordinates?: GpsCoordinate;
  geojson?: GeoJsonFeature;
  
  // Crop information
  current_crop?: string;
  planting_date?: string;
  expected_harvest_date?: string;
  
  // Status
  is_active: boolean;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}
