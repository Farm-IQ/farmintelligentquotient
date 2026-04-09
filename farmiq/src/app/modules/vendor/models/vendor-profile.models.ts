/**
 * VENDOR PROFILE MODELS
 * 
 * Role-specific profile for agricultural input vendors/suppliers
 */

import { UserProfile } from '../../auth/models/user-profile.models';

/**
 * Vendor role-specific profile
 * Stored in vendor_profiles table in Supabase
 */
export interface VendorProfile extends UserProfile {
  primary_role: 'vendor';
  
  vendor_profile: {
    id: string;
    user_id: string;
    
    // Business details
    business_name: string;
    business_type: 'input_supplier' | 'equipment_rental' | 'produce_buyer' | 'service_provider' | 'other';
    registration_number?: string;
    business_license_url?: string;
    
    // Products/Services
    products_categories?: string[]; // e.g., ['seeds', 'fertilizers', 'pesticides']
    main_products?: string[];
    service_areas?: string[]; // Regions covered
    
    // Location
    business_address?: string;
    business_location?: string;
    
    // Contact & hours
    business_phone?: string;
    business_email?: string;
    operating_hours?: {
      monday_to_friday?: string;
      saturday?: string;
      sunday?: string;
    };
    
    // Delivery/Service
    offers_delivery?: boolean;
    delivery_radius_km?: number;
    min_order_amount?: number;
    
    // Pricing & discounts
    bulk_discounts_available?: boolean;
    seasonal_products?: boolean;
    
    // Verification & ratings
    is_verified?: boolean;
    verified_at?: string;
    rating?: number;
    review_count?: number;
    
    // Bank account (for payments)
    bank_name?: string;
    account_holder?: string;
    account_number?: string; // Encrypted
    
    // Inventory
    inventory_managed?: boolean;
    stock_visibility?: boolean;
    
    // Timestamps
    created_at: string;
    updated_at: string;
  };
}

/**
 * Vendor profile update request
 */
export interface VendorProfileUpdateRequest {
  business_name?: string;
  business_type?: 'input_supplier' | 'equipment_rental' | 'produce_buyer' | 'service_provider' | 'other';
  business_address?: string;
  business_location?: string;
  business_phone?: string;
  business_email?: string;
  products_categories?: string[];
  main_products?: string[];
  service_areas?: string[];
  offers_delivery?: boolean;
  delivery_radius_km?: number;
  min_order_amount?: number;
}

/**
 * Product listing
 */
export interface VendorProduct {
  id: string;
  vendor_id: string;
  
  // Product details
  product_name: string;
  description?: string;
  category?: string;
  
  // Pricing
  unit_price: number;
  currency?: string;
  bulk_price?: number;
  
  // Inventory
  quantity_in_stock?: number;
  
  // Availability
  in_stock: boolean;
  available_from?: string;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}
