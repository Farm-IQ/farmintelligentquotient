/**
 * USER PROFILE MODELS
 * 
 * Base user profile interface that corresponds to the user_profiles table
 * This is the CENTRAL user profile that contains basic info and role assignment
 * 
 * Property names MUST match Supabase database schema exactly
 */

/**
 * Base user profile from database user_profiles table
 * This is the core user record that exists for every authenticated user
 */
export interface UserProfile {
  // Unique identifiers
  id: string; // UUID from auth.users, primary key
  farmiq_id: string; // UNIQUE custom identifier for FarmIQ platform
  
  // User information
  email: string;
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  
  // Profile status
  email_verified: boolean;
  profile_completed: boolean;
  
  // Role assignment (single primary role per user)
  primary_role: 'farmer' | 'cooperative' | 'lender' | 'agent' | 'vendor' | 'worker' | 'admin';
  
  // OAuth integration
  oauth_providers?: OAuthProvider[];
  
  // Profile picture
  avatar_url?: string;
  
  // Timestamps (must be ISO 8601 strings)
  created_at: string;
  updated_at: string;
  
  // Metadata
  metadata?: Record<string, any>;
}

/**
 * OAuth provider integration record
 */
export interface OAuthProvider {
  provider: string; // 'google', 'github', etc.
  provider_user_id: string;
  email?: string;
  name?: string;
  avatar_url?: string;
  linked_at: string;
}

/**
 * User profile with complete details including role-specific data
 * This is what you get when you fetch a user with their full profile
 */
export interface UserProfileComplete extends UserProfile {
  // Role-specific profile data (populated based on primary_role)
  farmer_profile?: any;
  cooperative_profile?: any;
  lender_profile?: any;
  agent_profile?: any;
  vendor_profile?: any;
  admin_profile?: any;
  
  // User roles/permissions
  user_roles?: UserRole[];
}

/**
 * Create/update request for user profile
 */
export interface UserProfileUpdateRequest {
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  avatar_url?: string;
  profile_completed?: boolean;
  metadata?: Record<string, any>;
}

/**
 * Profile response from database operations
 */
export interface UserProfileResponse {
  success: boolean;
  profile?: UserProfile;
  message?: string;
  error?: string;
}

// ============================================================================
// USER ROLE MODELS
// ============================================================================

/**
 * User role type - extends base UserProfile with role membership
 * Tracks which users have which roles
 */
export interface UserRole {
  id: string;
  user_id: string;
  role: 'farmer' | 'cooperative' | 'lender' | 'agent' | 'vendor' | 'worker' | 'admin';
  is_primary: boolean; // Is this the primary role for the user?
  
  // Role-specific metadata
  metadata?: Record<string, any>;
  
  // Assignment info
  assigned_by?: string; // Admin who assigned this role
  assigned_at: string;
  
  // Optional expiry for temporary roles
  expires_at?: string;
}

/**
 * Role assignment request
 */
export interface AssignRoleRequest {
  user_id: string;
  role: string;
  is_primary?: boolean;
  metadata?: Record<string, any>;
}

/**
 * Role assignment response
 */
export interface RoleAssignmentResponse {
  success: boolean;
  user_role?: UserRole;
  message?: string;
  error?: string;
}

// ============================================================================
// ROLE DEFINITIONS & PERMISSIONS
// ============================================================================

/**
 * Available roles in the system
 */
export enum UserRoleType {
  FARMER = 'farmer',
  COOPERATIVE = 'cooperative',
  LENDER = 'lender',
  AGENT = 'agent',
  VENDOR = 'vendor',
  WORKER = 'worker',
  ADMIN = 'admin'
}

/**
 * Role description and metadata
 */
export interface RoleDefinition {
  role: UserRoleType;
  label: string;
  description: string;
  icon?: string;
  color?: string;
  permissions: Permission[];
}

/**
 * Permission interface
 */
export interface Permission {
  name: string;
  description?: string;
  resource: string;
  action: 'create' | 'read' | 'update' | 'delete';
}

/**
 * Role-based access control
 */
export interface RolePermission {
  role: string;
  permissions: Permission[];
}

// ============================================================================
// PROFILE RESPONSE/STATE MODELS
// ============================================================================

/**
 * Profile load state (for tracking async operations)
 */
export interface ProfileLoadState {
  isLoading: boolean;
  isLoaded: boolean;
  error?: string;
  lastLoadTime?: number;
}

/**
 * User profile with load state (for reactive state management)
 */
export interface UserProfileState {
  profile?: UserProfile;
  isLoading: boolean;
  error?: string;
}

/**
 * Update profile result
 */
export interface UpdateProfileResult {
  success: boolean;
  profile?: UserProfile;
  error?: string;
  errors?: Record<string, string>; // Field-specific errors
}

// ============================================================================
// MIGRATION HELPER TYPES
// ============================================================================

/**
 * Email verification model matching database
 */
export interface EmailVerification {
  user_id: string;
  email: string;
  is_verified: boolean;
  verified_at?: string;
}
