/**
 * AGENT PROFILE MODELS
 * 
 * Role-specific profile for agricultural agents/extension officers
 */

import { UserProfile } from '../../auth/models/user-profile.models';

/**
 * Agent role-specific profile
 * Stored in agent_profiles table in Supabase
 */
export interface AgentProfile extends UserProfile {
  primary_role: 'agent';
  
  agent_profile: {
    id: string;
    user_id: string;
    
    // Agent details
    agent_type: 'extension_officer' | 'extension_agent' | 'field_officer' | 'input_supplier' | 'consultant';
    organization?: string; // Ministry, NGO, etc.
    
    // Coverage area
    assigned_region?: string;
    assigned_county?: string;
    assigned_ward?: string;
    
    // Specialization
    specializations?: string[]; // e.g., ['crop production', 'soil health', 'pest management']
    years_experience?: number;
    
    // License & certification
    license_number?: string;
    certification_body?: string;
    certification_date?: string;
    
    // Contact & service area
    service_phone?: string;
    service_email?: string;
    coverage_radius_km?: number; // Service radius
    
    // Performance metrics
    farmers_served?: number;
    average_rating?: number;
    successful_interventions?: number;
    
    // Verification
    is_verified?: boolean;
    verified_at?: string;
    
    // Timestamps
    created_at: string;
    updated_at: string;
  };
}

/**
 * Agent profile update request
 */
export interface AgentProfileUpdateRequest {
  agent_type?: 'extension_officer' | 'extension_agent' | 'field_officer' | 'input_supplier' | 'consultant';
  organization?: string;
  assigned_region?: string;
  assigned_county?: string;
  assigned_ward?: string;
  specializations?: string[];
  years_experience?: number;
  service_phone?: string;
  service_email?: string;
  coverage_radius_km?: number;
}

/**
 * Agent service/advisory record
 */
export interface AgentService {
  id: string;
  agent_id: string;
  farmer_id?: string; // If serving specific farmer
  
  // Service details
  service_type: 'consultation' | 'training' | 'diagnosis' | 'monitoring' | 'followup';
  service_category: string; // e.g., 'crop_health', 'soil_management'
  
  // Interaction details
  description: string;
  recommendations?: string;
  
  // Outcome
  outcome?: string;
  success_indicator?: string;
  
  // Scheduling
  service_date: string;
  follow_up_date?: string;
  
  // Media/attachments
  attachments?: string[]; // URLs to photos, documents
  
  // Timestamps
  created_at: string;
  updated_at: string;
}
