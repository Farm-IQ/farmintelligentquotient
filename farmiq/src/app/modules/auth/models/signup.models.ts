/**
 * SIGNUP & REGISTRATION MODELS
 * 
 * Models for user registration flow, including:
 * - Initial signup data
 * - Role selection
 * - Role-specific form data
 * - Signup responses
 */

// ============================================================================
// INITIAL SIGNUP REQUEST
// =============================================================================

/**
 * Initial signup request (email/password)
 */
export interface SignupRequest {
  email: string;
  password: string;
  password_confirm: string;
  accept_terms: boolean;
  accept_privacy: boolean;
}

/**
 * Complete signup data including role-specific information
 */
export interface SignupData {
  // Basic info
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  
  // Role selection
  selected_role: 'farmer' | 'cooperative' | 'lender' | 'agent' | 'vendor' | 'admin' | 'worker';
  
  // Role-specific data (one of these will be populated based on selected_role)
  farmer_data?: FarmerSignupData;
  cooperative_data?: CooperativeSignupData;
  lender_data?: LenderSignupData;
  agent_data?: AgentSignupData;
  vendor_data?: VendorSignupData;
  admin_data?: AdminSignupData;
  
  // Agreements
  accept_terms: boolean;
  accept_privacy: boolean;
  accept_newsletter?: boolean;
}

/**
 * Signup response after account creation
 */
export interface SignupResponse {
  success: boolean;
  message?: string;
  user_id?: string;
  email?: string;
  requires_email_verification?: boolean;
  verification_email_sent?: boolean;
  error?: string;
  errors?: Record<string, string[]>;
}

// ============================================================================
// ROLE-SPECIFIC SIGNUP DATA
// ============================================================================

/**
 * Farmer signup data
 */
export interface FarmerSignupData {
  farm_name: string;
  location: string;
  county: string;
  farm_size?: number;
  farming_method?: 'organic' | 'conventional' | 'mixed';
}

/**
 * Cooperative signup data
 */
export interface CooperativeSignupData {
  name?: string; // Alias for cooperative_name
  cooperative_name: string;
  cooperativeType?: string;
  registrationNumber?: string;
  member_count?: number;
  primary_commodity?: string;
  location?: string;
  county?: string;
}

/**
 * Lender signup data
 */
export interface LenderSignupData {
  institution_name: string;
  institution_type: 'bank' | 'microfinance' | 'cooperative' | 'government' | 'ngo' | 'other';
  min_loan_amount?: number;
  max_loan_amount?: number;
  county?: string;
  location?: string;
}

/**
 * Agent signup data
 */
export interface AgentSignupData {
  agent_type: 'extension_officer' | 'extension_agent' | 'field_officer' | 'input_supplier' | 'consultant';
  organization?: string;
  assigned_region?: string;
  county?: string;
  location?: string;
}

/**
 * Vendor signup data
 */
export interface VendorSignupData {
  business_name: string;
  business_type: 'input_supplier' | 'equipment_rental' | 'produce_buyer' | 'service_provider' | 'other';
  main_products?: string[];
  county?: string;
  location?: string;
}

/**
 * Admin signup data (not typically used, admins created by super_admin)
 */
export interface AdminSignupData {
  admin_level: 'super_admin' | 'regional_admin' | 'support_admin' | 'content_admin';
  department?: string;
}

// ============================================================================
// SIGNUP VALIDATION
// ============================================================================

/**
 * Validation error for signup field
 */
export interface SignupValidationError {
  field: string;
  message: string;
  code?: string;
}

/**
 * Signup validation result
 */
export interface SignupValidationResult {
  isValid: boolean;
  errors?: SignupValidationError[];
}

// ============================================================================
// EMAIL VERIFICATION AFTER SIGNUP
// ============================================================================

/**
 * Email verification request (user has email, needs to verify code)
 */
export interface VerifyEmailRequest {
  email: string;
  verification_code: string;
}

/**
 * Email verification response
 */
export interface VerifyEmailResponse {
  success: boolean;
  message?: string;
  email_verified?: boolean;
  error?: string;
}

/**
 * Resend verification code request
 */
export interface ResendVerificationCodeRequest {
  email: string;
}

/**
 * Resend verification code response
 */
export interface ResendVerificationCodeResponse {
  success: boolean;
  message?: string;
  code_sent?: boolean;
  error?: string;
}

// ============================================================================
// SIGNUP STATE (for UI/reactive management)
// ============================================================================

/**
 * Current signup step in multi-step process
 */
export enum SignupStep {
  INITIAL = 'initial',
  ROLE_SELECTION = 'role_selection',
  BASIC_INFO = 'basic_info',
  ROLE_SPECIFIC = 'role_specific',
  VERIFICATION = 'verification',
  COMPLETE = 'complete'
}

/**
 * Signup process state (for UI)
 */
export interface SignupProcessState {
  currentStep: SignupStep;
  completedSteps: SignupStep[];
  
  // Form data accumulated so far
  formData: Partial<SignupData>;
  
  // Validation errors
  validationErrors?: Record<string, string[]>;
  
  // Loading state
  isSubmitting: boolean;
  isVerifying: boolean;
  
  // Status
  isCompleted: boolean;
  isError: boolean;
  errorMessage?: string;
  
  // Last attempted action
  lastAction?: 'submit' | 'verify' | 'resend';
}

/**
 * Signup form configuration (what fields to show for each role)
 */
export interface RoleSignupFormConfig {
  role: string;
  fields: SignupFormField[];
  sections: SignupFormSection[];
}

/**
 * Form field definition
 */
export interface SignupFormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'checkbox' | 'textarea' | 'date';
  required: boolean;
  placeholder?: string;
  help_text?: string;
  options?: { label: string; value: any }[];
  validation?: {
    min_length?: number;
    max_length?: number;
    pattern?: string;
    custom?: (value: any) => boolean;
  };
}

/**
 * Form section (group of fields)
 */
export interface SignupFormSection {
  title: string;
  description?: string;
  fields: string[]; // Field names in this section
}

// ============================================================================
// SIGNUP COMPLETION
// ============================================================================

/**
 * Final signup completion response
 */
export interface SignupCompletionResponse {
  success: boolean;
  user_id: string;
  email: string;
  primary_role: string;
  farmiq_id: string;
  message?: string;
  next_step?: 'email_verification' | 'profile_completion' | 'dashboard' | 'onboarding';
  error?: string;
}
