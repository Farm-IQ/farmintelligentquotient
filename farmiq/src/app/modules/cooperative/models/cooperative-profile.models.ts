/**
 * COOPERATIVE PROFILE MODELS
 * 
 * Role-specific profile for cooperative organizations
 */

import { UserProfile } from '../../auth/models/user-profile.models';

/**
 * Cooperative role-specific profile
 * Stored in cooperative_profiles table in Supabase
 */
export interface CooperativeProfile extends UserProfile {
  primary_role: 'cooperative';
  
  cooperative_profile: {
    id: string;
    user_id: string;
    
    // Organization details
    cooperative_name: string;
    registration_number?: string;
    member_count?: number;
    location?: string;
    
    // Contact information
    office_address?: string;
    office_phone?: string;
    website?: string;
    
    // Operational details
    established_date?: string;
    primary_commodity?: string; // Main product/crop
    services_offered?: string[];
    
    // Verification
    is_registered?: boolean;
    registration_certificate_url?: string;
    is_verified?: boolean;
    verified_at?: string;
    
    // Bank account info (for payments)
    bank_name?: string;
    account_holder?: string;
    account_number?: string; // Encrypted
    
    // Ratings & performance
    rating?: number;
    total_transactions?: number;
    
    // Timestamps
    created_at: string;
    updated_at: string;
  };
}

/**
 * Cooperative profile update request
 */
export interface CooperativeProfileUpdateRequest {
  cooperative_name?: string;
  member_count?: number;
  location?: string;
  office_address?: string;
  office_phone?: string;
  website?: string;
  primary_commodity?: string;
  services_offered?: string[];
}

/**
 * Cooperative organization details
 */
export interface Cooperative {
  id: string;
  user_id: string;
  cooperative_name: string;
  registration_number?: string;
  member_count?: number;
  location?: string;
  office_address?: string;
  rating?: number;
  members: CooperativeMember[];
  created_at: string;
  updated_at: string;
}

/**
 * Cooperative member
 */
export interface CooperativeMember {
  id: string;
  cooperative_id: string;
  user_id: string;
  user_name: string;
  membership_status: 'active' | 'inactive' | 'suspended';
  joined_date: string;
  role_in_cooperative?: string;
}
