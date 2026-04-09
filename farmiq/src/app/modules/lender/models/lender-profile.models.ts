/**
 * LENDER PROFILE MODELS
 * 
 * Role-specific profile for financial lenders/institutions
 */

import { UserProfile } from '../../auth/models/user-profile.models';

/**
 * Lender role-specific profile
 * Stored in lender_profiles table in Supabase
 */
export interface LenderProfile extends UserProfile {
  primary_role: 'lender';
  
  lender_profile: {
    id: string;
    user_id: string;
    
    // Institution details
    institution_name: string;
    institution_type: 'bank' | 'microfinance' | 'cooperative' | 'government' | 'ngo' | 'other';
    license_number?: string;
    
    // Contact information
    office_address?: string;
    office_phone?: string;
    website?: string;
    
    // Lending details
    min_loan_amount?: number;
    max_loan_amount?: number;
    interest_rate_range?: {
      min: number;
      max: number;
    };
    loan_products?: string[]; // Types of loans offered
    lending_focus?: string[]; // e.g., ['agriculture', 'crop financing']
    
    // Verification & compliance
    is_registered?: boolean;
    registration_certificate_url?: string;
    is_verified?: boolean;
    verified_at?: string;
    
    // Performance metrics
    rating?: number;
    total_loans_disbursed?: number;
    total_amount_disbursed?: number;
    repayment_rate?: number; // Percentage
    
    // Bank account for disbursal
    bank_name?: string;
    account_holder?: string;
    account_number?: string; // Encrypted
    
    // Timestamps
    created_at: string;
    updated_at: string;
  };
}

/**
 * Lender profile update request
 */
export interface LenderProfileUpdateRequest {
  institution_name?: string;
  institution_type?: 'bank' | 'microfinance' | 'cooperative' | 'government' | 'ngo' | 'other';
  office_address?: string;
  office_phone?: string;
  website?: string;
  min_loan_amount?: number;
  max_loan_amount?: number;
  interest_rate_range?: {
    min: number;
    max: number;
  };
  loan_products?: string[];
  lending_focus?: string[];
}

/**
 * Loan application
 */
export interface LoanApplication {
  id: string;
  applicant_id: string; // Farmer ID
  lender_id: string;
  
  // Loan details
  loan_amount: number;
  loan_purpose: string;
  loan_duration_months: number;
  interest_rate: number;
  
  // Application status
  status: 'draft' | 'submitted' | 'under_review' | 'approved' | 'rejected' | 'disbursed' | 'closed';
  
  // Approval info
  approved_by?: string;
  approved_at?: string;
  rejection_reason?: string;
  
  // Timeline
  created_at: string;
  updated_at: string;
}
