/**
 * WORKER PROFILE MODELS
 * 
 * Role-specific profile for farm workers
 */

import { UserProfile } from '../../auth/models/user-profile.models';

/**
 * Worker role-specific profile
 * Stored in worker_profiles table in Supabase
 */
export interface WorkerProfile extends UserProfile {
  primary_role: 'worker';
  
  worker_profile: {
    id: string;
    user_id: string;
    farmiq_id: string;
    
    // Personal Information
    worker_name: string;
    phone_number: string;
    national_id?: string;
    marital_status?: string;
    next_of_kin?: string;
    
    // Farm & Employment Details
    farm_id?: string;
    role: string; // e.g., 'Farm Manager', 'Harvest Staff', 'Tractor Driver'
    department?: string;
    hire_date?: string;
    contract_type?: 'Permanent' | 'Temporary' | 'Seasonal' | 'Casual';
    
    // Contact Information
    emergency_contact?: string;
    emergency_contact_phone?: string;
    
    // Financial Information
    hourly_rate?: number;
    bank_account?: string;
    
    // Status
    is_active: boolean;
    is_deleted: boolean;
    
    // Timestamps
    created_at: string;
    updated_at: string;
  };
}

/**
 * Worker profile update request
 */
export interface WorkerProfileUpdateRequest {
  worker_name?: string;
  phone_number?: string;
  national_id?: string;
  marital_status?: string;
  next_of_kin?: string;
  role?: string;
  department?: string;
  contract_type?: 'Permanent' | 'Temporary' | 'Seasonal' | 'Casual';
  emergency_contact?: string;
  emergency_contact_phone?: string;
  hourly_rate?: number;
  bank_account?: string;
}

/**
 * Worker attendance record
 */
export interface WorkerAttendance {
  id: string;
  worker_id: string;
  farm_id: string;
  
  // Date information
  attendance_date?: string; // Made optional for flexibility
  date?: string; // Alias for attendance_date, also optional
  
  // Attendance details
  status: 'present' | 'absent' | 'late' | 'on_leave' | 'sick';
  check_in_time?: string;
  check_out_time?: string;
  hours_worked?: number;
  
  // Notes
  notes?: string;
  
  // Timestamps
  created_at: string;
}

/**
 * Worker payroll record
 */
export interface WorkerPayroll {
  id: string;
  worker_id: string;
  farm_id: string;
  
  // Payroll period
  payroll_period_start: string;
  payroll_period_end: string;
  
  // Pay details
  hours_worked: number;
  hourly_rate: number;
  base_salary?: number;
  allowances?: number;
  deductions?: number;
  overtime_hours?: number;
  overtime_rate?: number;
  gross_salary?: number;
  gross_pay: number;
  tax?: number;
  net_salary?: number;
  net_pay: number;
  
  // Payment info
  payment_method?: string;
  payment_date?: string;
  paid?: boolean;
  
  // Status
  status: 'pending' | 'processed' | 'paid';
  
  // Timestamps
  created_at: string;
  updated_at: string;
}

/**
 * Worker Performance - Periodic performance metrics
 */
export interface WorkerPerformance {
  id: string;
  worker_id: string;
  farm_id: string;
  evaluation_date: string;
  evaluated_by: string;
  category: 'productivity' | 'quality' | 'reliability' | 'teamwork' | 'leadership';
  score: number;
  max_score?: number;
  comments?: string;
  improvement_areas?: string[];
  strengths?: string[];
  next_review_date?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Worker Task - Task assignments and tracking
 */
export interface WorkerTask {
  id: string;
  worker_id: string;
  farm_id: string;
  task_name: string;
  description?: string;
  task_type: 'planting' | 'harvesting' | 'maintenance' | 'livestock_care' | 'equipment_operation' | 'other' | 'routine';
  assigned_by: string;
  assigned_date: string;
  due_date?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled' | 'assigned';
  notes?: string;
  completed_date?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Farm Worker - Reference for workers assigned to farms
 */
export interface FarmWorker {
  id: string;
  farm_id: string;
  worker_id: string;
  worker_name?: string;
  phone_number?: string;
  email?: string;
  national_id?: string;
  role: string;
  department?: string;
  hire_date: string;
  contract_type: 'Permanent' | 'Temporary' | 'Seasonal' | 'Casual';
  employment_type?: string;
  is_active: boolean;
  hourly_rate?: number;
  salary_amount?: number;
  salary_currency?: string;
  status?: 'active' | 'inactive' | 'suspended';
  emergency_contact?: string;
  emergency_phone?: string;
  address?: string;
  skills?: string[];
  certifications?: string[];
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Farm Worker Role Configuration
 */
export const FARM_WORKER_ROLES = [
  { value: 'Farm Manager', label: 'Farm Manager', description: 'Oversees all farm operations' },
  { value: 'Harvest Staff', label: 'Harvest Staff', description: 'Handles crop harvesting' },
  { value: 'Tractor Driver', label: 'Tractor Driver', description: 'Operates farm machinery' },
  { value: 'Livestock Handler', label: 'Livestock Handler', description: 'Manages farm animals' },
  { value: 'Irrigation Specialist', label: 'Irrigation Specialist', description: 'Manages water systems' },
  { value: 'General Laborer', label: 'General Laborer', description: 'Performs general farm tasks' }
];
