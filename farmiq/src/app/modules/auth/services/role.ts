import { Injectable, signal, computed, inject } from '@angular/core';
import { SupabaseService } from './supabase';
import { BehaviorSubject, Observable, Subject } from 'rxjs';

// Import from auth models
import {
  UserRole,
  UserRoleType,
  Permission,
  RoleDefinition,
  RoleAssignmentResponse
} from '../models/role.models';

/**
 * Role change event for cross-service communication
 */
export interface RoleChangeEvent {
  userId: string;
  role: UserRoleType;
  action: 'assign' | 'revoke';
  timestamp: Date;
}

@Injectable({
  providedIn: 'root',
})
export class RoleService {
  private supabase = inject(SupabaseService);
  
  // Angular Signals for reactive state
  private userRolesSignal = signal<UserRole[]>([]);
  private currentRoleSignal = signal<UserRoleType | null>(null);
  private hasAccessSignal = signal<boolean>(false);
  private permissionsSignal = signal<Permission[]>([]);
  private isLoadingSignal = signal<boolean>(false);
  private errorSignal = signal<string | null>(null);
  
  // Public computed signals (read-only)
  public userRoles$ = this.userRolesSignal.asReadonly();
  public currentRole$ = this.currentRoleSignal.asReadonly();
  public hasAccess$ = this.hasAccessSignal.asReadonly();
  public permissions$ = this.permissionsSignal.asReadonly();
  public isLoading$ = this.isLoadingSignal.asReadonly();
  public error$ = this.errorSignal.asReadonly();
  
  // Computed signal: Check if user has multiple roles
  public hasMultipleRoles = computed(() => this.userRolesSignal().length > 1);
  
  // Cross-service communication subject
  private roleChangeSubject = new Subject<RoleChangeEvent>();
  public roleChange$ = this.roleChangeSubject.asObservable();
  
  // Observable for backward compatibility
  private userRolesSubject = new BehaviorSubject<UserRole[]>([]);
  public userRoles = this.userRolesSubject.asObservable();

  constructor() {}

  /**
   * Get user roles from Supabase with signal updates
   * Fetches all roles assigned to a specific user
   */
  async getUserRoles(userId: string): Promise<Array<{ id: any; user_id: string; role: UserRoleType; assigned_at: any; is_active: any; is_primary: boolean }>> {
    try {
      this.isLoadingSignal.set(true);
      this.errorSignal.set(null);

      // Use public SupabaseService method to fetch user roles
      const userRoles = await this.supabase.getUserRoles(userId);

      // Transform database records to role assignment model
      const roles = (userRoles || []).map(ur => ({
        id: ur.id,
        user_id: userId,
        role: ur.role as UserRoleType,
        assigned_at: ur.assigned_at,
        is_active: ur.is_active,
        is_primary: false // Default: not primary, can be updated by caller if needed
      }));
      
      // Update signals - extract role types for signal
      this.userRolesSignal.set(roles.map(r => r.role as any));
      this.userRolesSubject.next(roles.map(r => r.role as any));
      
      console.log(`✅ Retrieved ${roles.length} roles for user ${userId}:`, roles.map(r => r.role));
      
      this.isLoadingSignal.set(false);
      return roles;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to get user roles';
      this.errorSignal.set(errorMsg);
      this.isLoadingSignal.set(false);
      console.error('Failed to get user roles:', error);
      return [];
    }
  }

  /**
   * Get permissions for a specific role
   * Returns list of permissions granted to the role
   */
  async getRolePermissions(role: UserRoleType): Promise<Permission[]> {
    try {
      // Map role to permissions
      const permissions = this.getPermissionsForRole(role);
      this.permissionsSignal.set(permissions);
      return permissions;
    } catch (error) {
      console.error('Failed to get role permissions:', error);
      return [];
    }
  }

  /**
   * Check if user has specific role
   * Verifies role existence in user's role list
   */
  async checkRoleAccess(userId: string, roleType: UserRoleType, module?: string): Promise<boolean> {
    try {
      console.log(`🔍 Checking role access - userId: ${userId}, role: ${roleType}, module: ${module}`);

      // Use public SupabaseService method to check user role
      const hasAccess = await this.supabase.checkUserRole(userId, roleType);
      
      console.log(`✅ Role access granted - ${roleType}: ${hasAccess}`);
      
      this.hasAccessSignal.set(hasAccess);
      return hasAccess;
    } catch (error) {
      console.error('Failed to check role access:', error);
      return false;
    }
  }

  /**
   * Assign role to user (admin only)
   * Creates new role assignment for user
   * Emits role change event for cross-service communication
   */
  async assignRole(request: {userId: string, role: UserRoleType}): Promise<RoleAssignmentResponse> {
    try {
      this.isLoadingSignal.set(true);
      this.errorSignal.set(null);

      // Call SupabaseService to assign role directly (no edge function call)
      await this.supabase.assignRoleToUser(request.userId, request.role as any);

      // Also update primary role if requested
      await this.supabase.updateUserPrimaryRole(request.userId, request.role);
      
      // Emit role change event for cross-service communication
      this.roleChangeSubject.next({
        userId: request.userId,
        role: request.role as UserRoleType,
        action: 'assign',
        timestamp: new Date()
      });

      this.isLoadingSignal.set(false);
      return {
        success: true,
        userId: request.userId,
        role: request.role,
        message: 'Role assigned successfully'
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to assign role';
      this.errorSignal.set(errorMsg);
      this.isLoadingSignal.set(false);
      console.error('Failed to assign role:', error);
      return {
        success: false,
        userId: request.userId,
        role: request.role,
        error: errorMsg
      };
    }
  }

  /**
   * Revoke role from user (admin only)
   * Removes role assignment from user
   * Emits role change event for cross-service communication
   */
  async revokeRole(userId: string, roleId: string): Promise<boolean> {
    try {
      this.isLoadingSignal.set(true);
      this.errorSignal.set(null);

      // Get the role type first so we can emit proper event
      const { data: userRole, error: queryError } = await this.supabase.getSupabaseClient()
        .then(client => client
          .from('user_roles')
          .select('role')
          .eq('id', roleId)
          .single()
        );

      if (queryError) {
        console.error('Error fetching role info:', queryError);
        this.errorSignal.set('Failed to fetch role information');
        this.isLoadingSignal.set(false);
        return false;
      }

      // Mark role as inactive (soft delete)
      const client = await this.supabase.getSupabaseClient();
      const { error: updateError } = await client
        .from('user_roles')
        .update({ is_active: false })
        .eq('id', roleId)
        .eq('user_id', userId);

      if (updateError) {
        console.error('Error revoking role:', updateError);
        this.errorSignal.set('Failed to revoke role');
        this.isLoadingSignal.set(false);
        return false;
      }
      
      // Emit role change event for cross-service communication
      this.roleChangeSubject.next({
        userId,
        role: (userRole?.role || 'farmer') as UserRoleType,
        action: 'revoke',
        timestamp: new Date()
      });

      this.isLoadingSignal.set(false);
      return true;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to revoke role';
      this.errorSignal.set(errorMsg);
      this.isLoadingSignal.set(false);
      console.error('Failed to revoke role:', error);
      return false;
    }
  }

  /**
   * Get all available role definitions
   * Returns list of role definitions with permissions
   */
  async getAllRoles(): Promise<RoleDefinition[]> {
    try {
      return [
        {
          name: 'farmer' as UserRoleType,
          label: 'Farmer',
          description: 'Smallholder farmer user',
          permissions: this.getPermissionsForRole('farmer' as UserRoleType),
          modules: ['dashboard', 'farm-management', 'chatbot']
        },
        {
          name: 'cooperative' as UserRoleType,
          label: 'Cooperative',
          description: 'Farmer cooperative organization',
          permissions: this.getPermissionsForRole('cooperative' as UserRoleType),
          modules: ['members', 'marketplace']
        },
        {
          name: 'lender' as UserRoleType,
          label: 'Lender',
          description: 'Financial institution',
          permissions: this.getPermissionsForRole('lender' as UserRoleType),
          modules: ['loans', 'applications']
        },
        {
          name: 'agent' as UserRoleType,
          label: 'Agent',
          description: 'Extension officer/agent',
          permissions: this.getPermissionsForRole('agent' as UserRoleType),
          modules: ['farmers', 'advisory']
        },
        {
          name: 'vendor' as UserRoleType,
          label: 'Vendor',
          description: 'Input supplier/vendor',
          permissions: this.getPermissionsForRole('vendor' as UserRoleType),
          modules: ['products', 'orders']
        },
        {
          name: 'admin' as UserRoleType,
          label: 'Admin',
          description: 'System administrator',
          permissions: this.getPermissionsForRole('admin' as UserRoleType),
          modules: ['users', 'roles', 'analytics', 'settings']
        }
      ];
    } catch (error) {
      console.error('Failed to get all roles:', error);
      return [];
    }
  }

  /**
   * Get permissions for a specific role
   * Helper method that maps roles to their permissions
   */
  private getPermissionsForRole(role: UserRoleType): Permission[] {
    const rolePermissions: Record<UserRoleType, Permission[]> = {
      farmer: [
        { id: 'farm_view_profile', name: 'view_profile', description: 'View own profile', category: 'read' },
        { id: 'farm_edit_profile', name: 'edit_profile', description: 'Edit own profile', category: 'update' },
        { id: 'farm_view_farm', name: 'view_farm', description: 'View farm information', category: 'read' },
        { id: 'farm_edit_farm', name: 'edit_farm', description: 'Edit farm information', category: 'update' },
        { id: 'farm_access_chatbot', name: 'access_chatbot', description: 'Access FarmGrow chatbot', category: 'read' },
        { id: 'farm_view_farmscore', name: 'view_farmscore', description: 'View farm score assessment', category: 'read' }
      ],
      cooperative: [
        { id: 'coop_view_members', name: 'view_members', description: 'View cooperative members', category: 'read' },
        { id: 'coop_manage_members', name: 'manage_members', description: 'Manage cooperative members', category: 'update' },
        { id: 'coop_view_marketplace', name: 'view_marketplace', description: 'View marketplace', category: 'read' },
        { id: 'coop_list_products', name: 'list_products', description: 'List products in marketplace', category: 'create' }
      ],
      lender: [
        { id: 'lend_view_applications', name: 'view_applications', description: 'View loan applications', category: 'read' },
        { id: 'lend_approve_loans', name: 'approve_loans', description: 'Approve loan applications', category: 'update' },
        { id: 'lend_disburse_funds', name: 'disburse_funds', description: 'Disburse loan funds', category: 'create' },
        { id: 'lend_manage_products', name: 'manage_products', description: 'Manage loan products', category: 'update' }
      ],
      agent: [
        { id: 'agent_view_farmers', name: 'view_farmers', description: 'View assigned farmers', category: 'read' },
        { id: 'agent_log_services', name: 'log_services', description: 'Log extension services', category: 'create' },
        { id: 'agent_access_chatbot', name: 'access_chatbot', description: 'Access chatbot for advisory', category: 'read' }
      ],
      vendor: [
        { id: 'vend_manage_products', name: 'manage_products', description: 'Manage product listings', category: 'update' },
        { id: 'vend_view_orders', name: 'view_orders', description: 'View customer orders', category: 'read' },
        { id: 'vend_manage_orders', name: 'manage_orders', description: 'Manage order fulfillment', category: 'update' }
      ],
      worker: [
        { id: 'work_view_profile', name: 'view_profile', description: 'View own profile', category: 'read' },
        { id: 'work_edit_profile', name: 'edit_profile', description: 'Edit own profile', category: 'update' },
        { id: 'work_view_assignments', name: 'view_assignments', description: 'View work assignments', category: 'read' },
        { id: 'work_log_attendance', name: 'log_attendance', description: 'Log attendance and hours', category: 'create' },
        { id: 'work_view_payroll', name: 'view_payroll', description: 'View payroll information', category: 'read' }
      ],
      admin: [
        { id: 'admin_manage_users', name: 'manage_users', description: 'Manage all users', category: 'update' },
        { id: 'admin_manage_roles', name: 'manage_roles', description: 'Manage user roles', category: 'update' },
        { id: 'admin_approve_vendors', name: 'approve_vendors', description: 'Approve vendor registrations', category: 'update' },
        { id: 'admin_approve_lenders', name: 'approve_lenders', description: 'Approve lender registrations', category: 'update' },
        { id: 'admin_access_analytics', name: 'access_analytics', description: 'Access platform analytics', category: 'read' },
        { id: 'admin_manage_system', name: 'manage_system', description: 'Manage system settings', category: 'update' }
      ]
    };

    return rolePermissions[role] || [];
  }
}
