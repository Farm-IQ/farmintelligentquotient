import { Injectable, inject } from '@angular/core';
import { SupabaseService } from '../core/supabase.service';

/**
 * Permission Service
 * Handles resource-level permission checks using check-role-access-native
 * Use this before making API calls that require specific permissions
 * 
 * Example:
 * - Before creating a conversation: checkPermission('conversations', 'create')
 * - Before reading messages: checkPermission('messages', 'read')
 * - Before updating a farm: checkPermission('farms', 'update')
 */
@Injectable({
  providedIn: 'root',
})
export class PermissionService {
  private supabase = inject(SupabaseService);
  
  // Cache for permission checks (avoid excessive API calls)
  private permissionCache = new Map<string, { allowed: boolean; timestamp: number }>();
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes

  /**
   * Check if user has permission for a specific resource and action
   * Uses cached results to avoid excessive API calls
   * 
   * @param resource - Resource name (e.g., 'conversations', 'farms', 'messages')
   * @param action - Action type (e.g., 'read', 'create', 'update', 'delete')
   * @returns true if user has permission, false otherwise
   */
  async checkPermission(resource: string, action: string): Promise<boolean> {
    const cacheKey = `${resource}:${action}`;
    
    // Check cache first
    const cached = this.permissionCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
      console.log(`📦 Using cached permission: ${cacheKey} = ${cached.allowed}`);
      return cached.allowed;
    }

    // Call the actual permission check
    const allowed = await this.supabase.checkResourcePermission(resource, action);
    
    // Cache the result
    this.permissionCache.set(cacheKey, {
      allowed,
      timestamp: Date.now(),
    });

    return allowed;
  }

  /**
   * Check multiple permissions at once
   * Returns object with results for each permission
   * 
   * @param permissions - Array of {resource, action} tuples
   * @returns Object with permission check results
   */
  async checkPermissions(
    permissions: Array<{ resource: string; action: string }>
  ): Promise<Record<string, boolean>> {
    const results: Record<string, boolean> = {};
    
    for (const { resource, action } of permissions) {
      const key = `${resource}:${action}`;
      results[key] = await this.checkPermission(resource, action);
    }
    
    return results;
  }

  /**
   * Assert permission - throw error if user doesn't have permission
   * Use this in services before making API calls
   * 
   * @param resource - Resource name
   * @param action - Action type
   * @throws Error if permission denied
   */
  async assertPermission(resource: string, action: string): Promise<void> {
    const allowed = await this.checkPermission(resource, action);
    if (!allowed) {
      throw new Error(`Permission denied: cannot ${action} ${resource}`);
    }
  }

  /**
   * Invalidate permission cache
   * Call this after role changes or permission updates
   */
  invalidateCache(): void {
    console.log('🔄 Invalidating permission cache');
    this.permissionCache.clear();
  }

  /**
   * Invalidate specific permission cache entry
   * 
   * @param resource - Resource name
   * @param action - Action type
   */
  invalidateCacheEntry(resource: string, action: string): void {
    const cacheKey = `${resource}:${action}`;
    this.permissionCache.delete(cacheKey);
    console.log(`🔄 Invalidated cache entry: ${cacheKey}`);
  }

  /**
   * Common resource permissions (for reference)
   * These align with your role-based permission matrix
   */
  static readonly RESOURCES = {
    CONVERSATIONS: 'conversations',
    FARMS: 'farms',
    CROPS: 'crops',
    DOCUMENTS: 'documents',
    MESSAGES: 'messages',
    COOPERATIVE_MEMBERS: 'cooperative_members',
  } as const;

  static readonly ACTIONS = {
    READ: 'read',
    CREATE: 'create',
    UPDATE: 'update',
    DELETE: 'delete',
  } as const;
}
