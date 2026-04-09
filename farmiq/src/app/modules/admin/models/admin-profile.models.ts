/**
 * ADMIN PROFILE MODELS
 * 
 * Role-specific profile for system administrators
 */

import { UserProfile } from '../../auth/models/user-profile.models';

/**
 * Admin role-specific profile
 * Stored in admin_profiles table in Supabase
 */
export interface AdminProfile extends UserProfile {
  primary_role: 'admin';
  
  admin_profile: {
    id: string;
    user_id: string;
    
    // Admin details
    admin_level: 'super_admin' | 'regional_admin' | 'support_admin' | 'content_admin';
    admin_department?: string;
    
    // Permissions
    can_manage_users: boolean;
    can_manage_roles: boolean;
    can_approve_vendors: boolean;
    can_approve_lenders: boolean;
    can_manage_content: boolean;
    can_access_analytics: boolean;
    can_manage_system_settings: boolean;
    
    // Scope/responsibility
    assigned_region?: string;
    assigned_county?: string;
    all_regions?: boolean; // Can access all regions
    
    // Employment info
    employee_id?: string;
    department?: string;
    manager_id?: string;
    
    // Contact info
    office_phone?: string;
    office_address?: string;
    
    // Activity logging
    last_login?: string;
    login_count?: number;
    
    // Status
    is_active: boolean;
    suspension_reason?: string;
    
    // Timestamps
    created_at: string;
    updated_at: string;
  };
}

/**
 * Admin profile update request
 */
export interface AdminProfileUpdateRequest {
  admin_level?: 'super_admin' | 'regional_admin' | 'support_admin' | 'content_admin';
  admin_department?: string;
  assigned_region?: string;
  assigned_county?: string;
  office_phone?: string;
  office_address?: string;
  is_active?: boolean;
}

/**
 * Admin action log for audit trail
 */
export interface AdminActionLog {
  id: string;
  admin_id: string;
  
  // Action details
  action: string; // e.g., 'user_created', 'role_assigned', 'content_approved'
  resource_type: string; // e.g., 'user', 'vendor', 'document'
  resource_id: string;
  
  // Change details
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  
  // Metadata
  ip_address?: string;
  user_agent?: string;
  
  // Timestamp
  created_at: string;
}

/**
 * System settings (managed by admins)
 */
export interface SystemSettings {
  id: string;
  setting_key: string;
  setting_value: any;
  description?: string;
  updated_by?: string;
  created_at: string;
  updated_at: string;
}
