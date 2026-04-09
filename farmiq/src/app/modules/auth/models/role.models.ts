/**
 * Role & Authorization Models
 * Role definitions, permissions, and access control
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

export type UserRole = UserRoleType;

export interface RoleDefinition {
  name: UserRole;
  label: string;
  description: string;
  permissions: Permission[];
  modules: string[];
}

export interface Permission {
  id: string;
  name: string;
  description: string;
  category: 'read' | 'create' | 'update' | 'delete' | 'execute';
}

export interface RoleChangeEvent {
  userId: string;
  role: UserRole;
  action: 'assign' | 'revoke' | 'update';
  timestamp: Date;
}

export interface RoleAssignmentRequest {
  userId: string;
  role: UserRole;
  metadata?: Record<string, any>;
}

export interface RoleAssignmentResponse {
  success: boolean;
  userId: string;
  role: UserRole;
  message?: string;
  error?: string;
}
