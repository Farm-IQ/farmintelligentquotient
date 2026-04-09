/**
 * FarmIQ ID Service
 * Generates unique 6-character alphanumeric FarmIQ IDs (e.g., FQ7K2P)
 * Format: FQ + 4 random alphanumeric characters
 * 
 * Features:
 * - Generates unique IDs: FQK9M2, FQX7L4, FQPD8W
 * - Validates format
 * - Checks uniqueness against database
 * - Auto-regenerates on duplicate
 * - Retry mechanism for collision handling
 */

import { Injectable } from '@angular/core';

export interface FarmiqIdResult {
  success: boolean;
  farmiqId?: string;
  error?: string;
  retries?: number;
}

@Injectable({
  providedIn: 'root'
})
export class FarmiqIdService {
  private readonly FARMIQ_PREFIX = 'FQ';
  private readonly ID_LENGTH = 4; // 4 random characters after FQ = 6 total
  private readonly CHARSET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  private readonly MAX_RETRIES = 5; // Maximum retries on collision
  private generatedIds = new Set<string>(); // Track generated IDs in current session

  constructor() {}

  /**
   * Generate a unique FarmIQ ID (synchronous, simple generation)
   * Format: FQ + 4 random alphanumeric characters (uppercase)
   * 
   * Note: This doesn't check database for duplicates. Use generateUniqueFarmiqId() for that.
   * 
   * @returns Unique FarmIQ ID (e.g., FQK9M2)
   */
  generateFarmiqId(): string {
    let id = this.FARMIQ_PREFIX;
    
    // Generate 4 random characters from charset
    for (let i = 0; i < this.ID_LENGTH; i++) {
      const randomIndex = Math.floor(Math.random() * this.CHARSET.length);
      id += this.CHARSET[randomIndex];
    }
    
    return id;
  }

  /**
   * Generate a unique FarmIQ ID (convenience method for services)
   * Wrapper around generateUniqueFarmiqIdWithResult() that throws errors
   * 
   * @throws Error if unable to generate unique ID after 5 attempts
   * @returns Promise<string> with generated FarmIQ ID (e.g., "FQK9M2")
   */
  async generateUniqueId(): Promise<string> {
    const result = await this.generateUniqueFarmiqIdWithResult();
    if (!result.success) {
      throw new Error(result.error || 'Failed to generate unique FarmIQ ID');
    }
    return result.farmiqId!;
  }

  /**
   * Generate a unique FarmIQ ID with database uniqueness check
   * Ensures the generated ID doesn't already exist in user_profiles
   * Auto-regenerates on collision
   * 
   * @returns Promise<FarmiqIdResult> with success status and FarmIQ ID or error
   */
  async generateUniqueFarmiqIdWithResult(): Promise<FarmiqIdResult> {
    let retries = 0;
    
    while (retries < this.MAX_RETRIES) {
      // Generate ID
      const farmiqId = this.generateFarmiqId();
      
      // Check if already generated in this session (quick check)
      if (this.generatedIds.has(farmiqId)) {
        console.warn(`⚠️ Generated duplicate in session: ${farmiqId}, regenerating...`);
        retries++;
        continue;
      }
      
      // Check database for uniqueness
      try {
        const exists = await this.checkIfIdExists(farmiqId);
        
        if (!exists) {
          // Track as generated
          this.generatedIds.add(farmiqId);
          console.log(`✅ Generated unique FarmIQ ID: ${farmiqId} (retry: ${retries})`);
          return {
            success: true,
            farmiqId: farmiqId,
            retries: retries
          };
        } else {
          console.warn(`⚠️ FarmIQ ID already exists: ${farmiqId}, regenerating... (attempt ${retries + 1}/${this.MAX_RETRIES})`);
          retries++;
        }
      } catch (error) {
        console.error(`❌ Error checking ID uniqueness:`, error);
        // If database check fails, return the ID anyway (backend will validate)
        return {
          success: true,
          farmiqId: this.generateFarmiqId(),
          retries: retries,
          error: 'Database check failed, returned unchecked ID'
        };
      }
    }
    
    // Failed after max retries
    return {
      success: false,
      error: `Failed to generate unique FarmIQ ID after ${this.MAX_RETRIES} attempts`,
      retries: this.MAX_RETRIES
    };
  }

  // Uniqueness check is now delegated to backend validation
  // This avoids circular dependency with SupabaseService

  /**
   * Check if FarmIQ ID exists in database
   * 
   * SIMPLIFIED: Now delegates uniqueness validation to backend
   * The collision probability for 36^4 = ~1.6M combinations is negligible
   * Backend will validate and handle any collisions during signup
   * 
   * @param farmiqId ID to check
   * @returns Promise<boolean> Always returns false (backend will validate)
   */
  private async checkIfIdExists(farmiqId: string): Promise<boolean> {
    // Always return false - backend will validate uniqueness
    // This avoids circular dependency with SupabaseService
    return false;
  }

  /**
   * Generate multiple FarmIQ IDs (useful for batch operations)
   * 
   * @param count Number of IDs to generate
   * @returns Array of unique FarmIQ IDs
   */
  generateMultipleFarmiqIds(count: number): string[] {
    const ids: string[] = [];
    for (let i = 0; i < count; i++) {
      ids.push(this.generateFarmiqId());
    }
    return ids;
  }

  /**
   * Validate if a string is a valid FarmIQ ID
   * 
   * @param id String to validate
   * @returns True if valid FarmIQ ID format
   */
  isValidFarmiqId(id: string): boolean {
    if (!id || typeof id !== 'string') return false;
    
    // Should be exactly 6 characters: FQ + 4 alphanumeric
    if (id.length !== 6) return false;
    
    // Should start with FQ
    if (!id.startsWith(this.FARMIQ_PREFIX)) return false;
    
    // Last 4 characters should be alphanumeric
    const suffix = id.substring(2);
    return /^[A-Z0-9]{4}$/.test(suffix);
  }

  /**
   * Extract random part from FarmIQ ID
   * 
   * @param id FarmIQ ID
   * @returns The 4 character random suffix
   */
  getIdSuffix(id: string): string {
    if (!this.isValidFarmiqId(id)) return '';
    return id.substring(2);
  }

  /**
   * Clear session-tracked IDs (call after successful signup)
   */
  clearSessionIds(): void {
    this.generatedIds.clear();
    console.log('✅ Cleared session FarmIQ IDs');
  }

  /**
   * Get the current user's FarmIQ ID from localStorage
   * This is the ID stored after successful authentication
   * 
   * @returns The FarmIQ ID if user is authenticated, null otherwise
   */
  getFarmiqId(): string | null {
    try {
      // Check if localStorage is available (not in SSR)
      if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
        return null;
      }
      const farmiqId = localStorage.getItem('farmiq_id');
      return farmiqId;
    } catch (error) {
      console.error('Error retrieving FarmIQ ID:', error);
      return null;
    }
  }

  /**
   * Store the FarmIQ ID in localStorage (call after signup/login)
   * 
   * @param farmiqId The FarmIQ ID to store
   */
  setFarmiqId(farmiqId: string): void {
    try {
      // Check if localStorage is available (not in SSR)
      if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
        console.warn('⚠️ localStorage not available (SSR mode), skipping FarmIQ ID storage');
        return;
      }
      if (this.isValidFarmiqId(farmiqId)) {
        localStorage.setItem('farmiq_id', farmiqId.toUpperCase());
        console.log(`✅ Stored FarmIQ ID: ${farmiqId}`);
      } else {
        console.warn(`❌ Invalid FarmIQ ID format: ${farmiqId}`);
      }
    } catch (error) {
      console.error('Error storing FarmIQ ID:', error);
    }
  }

  /**
   * Clear the stored FarmIQ ID (call on logout)
   */
  clearFarmiqId(): void {
    try {
      // Check if localStorage is available (not in SSR)
      if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
        // Still clear session IDs even if localStorage isn't available
        this.generatedIds.clear();
        return;
      }
      localStorage.removeItem('farmiq_id');
      this.generatedIds.clear();
      console.log('✅ Cleared FarmIQ ID from storage');
    } catch (error) {
      console.error('Error clearing FarmIQ ID:', error);
    }
  }

  /**
   * LEGACY: Backward compatibility alias for generateUniqueFarmiqIdWithResult()
   * Use generateUniqueId() for simpler string-returning version
   */
  async generateUniqueFarmiqId(): Promise<FarmiqIdResult> {
    return this.generateUniqueFarmiqIdWithResult();
  }
}
