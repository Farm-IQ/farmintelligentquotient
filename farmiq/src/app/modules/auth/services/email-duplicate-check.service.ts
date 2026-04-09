/**
 * Email Duplicate Check Service
 * 
 * Checks for existing emails in the system before signup
 * Provides suggestions for email variations if a duplicate is found
 * Caches results to prevent excessive API calls
 * 
 * Usage in signup component:
 * ```typescript
 * constructor(private emailDuplicateCheck: EmailDuplicateCheckService) {}
 * 
 * async checkEmail(email: string): Promise<void> {
 *   const result = await this.emailDuplicateCheck.checkEmail(email);
 *   if (!result.available) {
 *     this.errorMessage = result.message;
 *     this.emailSuggestions = result.suggestions || [];
 *   }
 * }
 * ```
 */

import { Injectable } from '@angular/core';
import { SupabaseClient } from '@supabase/supabase-js';
import { SupabaseService } from './supabase';

export interface EmailCheckResult {
  available: boolean;
  message: string;
  suggestions?: string[];
  cached: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class EmailDuplicateCheckService {
  private emailCache = new Map<string, { result: EmailCheckResult; timestamp: number }>();
  private readonly CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes
  private readonly MAX_SUGGESTIONS = 5;

  constructor(private supabase: SupabaseService) {
    // Clean up expired cache entries every 10 minutes
    setInterval(() => this.cleanupExpiredCache(), 10 * 60 * 1000);
  }

  /**
   * Check if email is available (not already registered)
   * Returns cached result if still valid, otherwise queries database
   */
  async checkEmail(email: string): Promise<EmailCheckResult> {
    if (!email) {
      return {
        available: false,
        message: 'Email is required',
        cached: false,
      };
    }

    const normalizedEmail = email.toLowerCase().trim();

    // Check cache first
    const cached = this.emailCache.get(normalizedEmail);
    if (cached && Date.now() - cached.timestamp < this.CACHE_TTL_MS) {
      console.log(`📦 Email check result from cache (${Math.round((this.CACHE_TTL_MS - (Date.now() - cached.timestamp)) / 1000)}s remaining)`);
      return { ...cached.result, cached: true };
    }

    try {
      // Query Supabase to check if email exists in user_profiles
      const client = await this.supabase.getSupabaseClient();
      const { data, error } = await client
        .from('user_profiles')
        .select('email')
        .eq('email', normalizedEmail)
        .maybeSingle();

      let result: EmailCheckResult;

      if (error) {
        console.warn('Error checking email availability:', error);
        // On error, allow signup to proceed (better UX than blocking)
        result = {
          available: true,
          message: 'Could not verify email availability. You can continue.',
          cached: false,
        };
      } else if (data) {
        // Email exists - not available
        result = {
          available: false,
          message: `❌ The email ${email} is already registered. Please use a different email or try logging in.`,
          suggestions: await this.generateEmailSuggestions(normalizedEmail),
          cached: false,
        };
      } else {
        // No data means email is available
        result = {
          available: true,
          message: `✅ Email ${email} is available!`,
          cached: false,
        };
      }

      // Cache the result
      this.emailCache.set(normalizedEmail, {
        result,
        timestamp: Date.now(),
      });

      return result;
    } catch (error) {
      console.error('Unexpected error checking email:', error);
      // On error, allow signup to proceed
      return {
        available: true,
        message: 'Could not verify email availability. You can continue.',
        cached: false,
      };
    }
  }

  /**
   * Generate email suggestions based on variations of the original email
   * Examples: john+1@gmail.com, john.farmer@gmail.com, johnsmith2@gmail.com
   */
  private async generateEmailSuggestions(email: string): Promise<string[]> {
    const suggestions = new Set<string>();
    const [localPart, domain] = email.split('@');

    // 1. Add +1, +2, +3 variations
    for (let i = 1; i <= 3; i++) {
      suggestions.add(`${localPart}+${i}@${domain}`);
    }

    // 2. Add role suffixes (farmer, coop, lender)
    const roleSuffixes = ['farmer', 'coop', 'lender', 'agent', 'vendor'];
    for (const role of roleSuffixes) {
      const withRole = `${localPart}+${role}@${domain}`;
      if (!suggestions.has(withRole)) {
        suggestions.add(withRole);
      }
    }

    // 3. Add numbered variants
    for (let i = 2; i <= 4; i++) {
      suggestions.add(`${localPart}${i}@${domain}`);
    }

    // Convert Set to Array and limit to MAX_SUGGESTIONS
    const suggestionArray = Array.from(suggestions).slice(0, this.MAX_SUGGESTIONS);

    // Check which suggestions are actually available (verify top 3-5)
    const availableSuggestions: string[] = [];
    for (const suggestion of suggestionArray.slice(0, 3)) {
      const check = await this.checkEmailQuick(suggestion);
      if (check.available) {
        availableSuggestions.push(suggestion);
        if (availableSuggestions.length >= 3) break; // Get at least 3 available suggestions
      }
    }

    // If not enough verified suggestions, add unverified ones
    if (availableSuggestions.length < 3) {
      for (const suggestion of suggestionArray) {
        if (!availableSuggestions.includes(suggestion)) {
          availableSuggestions.push(suggestion);
          if (availableSuggestions.length >= this.MAX_SUGGESTIONS) break;
        }
      }
    }

    return availableSuggestions.slice(0, this.MAX_SUGGESTIONS);
  }

  /**
   * Quick email availability check (used for suggestions)
   * Does not cache results to keep logic simple
   */
  private async checkEmailQuick(email: string): Promise<{ available: boolean }> {
    try {
      const client = await this.supabase.getSupabaseClient();
      const { error } = await client
        .from('user_profiles')
        .select('email', { count: 'exact', head: true })
        .eq('email', email.toLowerCase().trim());

      // If we get PGRST116, no rows found, email is available
      if (error && error.code === 'PGRST116') {
        return { available: true };
      }

      // If no error, email exists, so not available
      return { available: !error || error.code === 'PGRST116' };
    } catch {
      // On error, assume not available to be safe
      return { available: false };
    }
  }

  /**
   * Invalidate cache for specific email
   * Call this after successful signup to prevent false positives
   */
  invalidateCache(email: string): void {
    const normalizedEmail = email.toLowerCase().trim();
    this.emailCache.delete(normalizedEmail);
    console.log(`🗑️  Email cache invalidated for ${normalizedEmail}`);
  }

  /**
   * Clear all cached email checks
   */
  clearCache(): void {
    this.emailCache.clear();
    console.log('🗑️  All email cache cleared');
  }

  /**
   * Get cache statistics for debugging
   */
  getCacheStats(): { size: number; entries: string[] } {
    return {
      size: this.emailCache.size,
      entries: Array.from(this.emailCache.keys()),
    };
  }

  /**
   * Clean up expired cache entries
   */
  private cleanupExpiredCache(): void {
    const now = Date.now();
    let cleanedCount = 0;

    for (const [email, { timestamp }] of this.emailCache.entries()) {
      if (now - timestamp > this.CACHE_TTL_MS) {
        this.emailCache.delete(email);
        cleanedCount++;
      }
    }

    if (cleanedCount > 0) {
      console.log(`🧹 Email cache cleanup: Removed ${cleanedCount} expired entries`);
    }
  }
}
