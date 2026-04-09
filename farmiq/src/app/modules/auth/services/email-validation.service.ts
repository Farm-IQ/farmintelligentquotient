import { Injectable } from '@angular/core';
import { SupabaseService } from './supabase';

/**
 * Email Validation Service (CONSOLIDATED)
 * Provides real-time email validation, duplicate detection, and suggestions
 * Prevents invalid/duplicate email registration
 * 
 * Merged from:
 * - email-validation.service.ts (format validation, availability checks)
 * - email-duplicate-check.service.ts (duplicate detection, suggestions)
 */
export interface EmailCheckResult {
  available: boolean;
  message: string;
  suggestions?: string[];
  cached: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class EmailValidationService {
  private emailCache = new Map<string, { result: boolean; timestamp: number }>();
  private checkResultCache = new Map<string, { result: EmailCheckResult; timestamp: number }>();
  private readonly EMAIL_CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes
  private readonly CACHE_CLEANUP_INTERVAL_MS = 10 * 60 * 1000; // 10 minutes
  private readonly MAX_SUGGESTIONS = 5;
  private cacheCleanupInterval: any;

  constructor(private supabase: SupabaseService) {
    // Clean cache periodically
    this.cacheCleanupInterval = setInterval(() => this.cleanupCache(), this.CACHE_CLEANUP_INTERVAL_MS);
  }

  ngOnDestroy(): void {
    if (this.cacheCleanupInterval) {
      clearInterval(this.cacheCleanupInterval);
    }
  }

  /**
   * Check if email is available (not yet registered)
   * Uses cache to reduce database queries
   * Combines format validation + availability check
   */
  async isEmailAvailable(email: string): Promise<boolean> {
    const normalized = email.toLowerCase().trim();

    if (!normalized) {
      return false;
    }

    // Check cache first (simple boolean cache)
    const cached = this.emailCache.get(normalized);
    if (cached && Date.now() - cached.timestamp < this.EMAIL_CACHE_TTL_MS) {
      console.log(`📦 Email availability cache hit for ${normalized}`);
      return cached.result;
    }

    try {
      // Query database
      const client = await this.supabase.getSupabaseClient();
      const { data, error } = await client
        .from('user_profiles')
        .select('id')
        .eq('email', normalized)
        .maybeSingle();

      // Email is available if no results and no errors
      const available = !data && !error;

      // Cache result with timestamp
      this.emailCache.set(normalized, { result: available, timestamp: Date.now() });

      return available;
    } catch (error) {
      console.error('Email availability check failed:', error);
      // Assume email is available on error (better UX than blocking)
      return true;
    }
  }

  /**
   * Complete email check: format + availability + suggestions (CONSOLIDATED)
   * Combines all validation logic in one method
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

    // Check comprehensive result cache first
    const cached = this.checkResultCache.get(normalizedEmail);
    if (cached && Date.now() - cached.timestamp < this.EMAIL_CACHE_TTL_MS) {
      console.log(`📦 Email check result from cache`);
      return { ...cached.result, cached: true };
    }

    // Step 1: Validate format
    const formatValidation = this.validateEmailFormat(normalizedEmail);
    if (!formatValidation.valid) {
      const result: EmailCheckResult = {
        available: false,
        message: formatValidation.error || 'Invalid email format',
        cached: false,
      };
      this.checkResultCache.set(normalizedEmail, { result, timestamp: Date.now() });
      return result;
    }

    // Step 2: Check if email already exists
    const available = await this.isEmailAvailable(normalizedEmail);

    if (!available) {
      // Email is taken - provide suggestions
      const suggestions = await this.getEmailSuggestions(email);
      const result: EmailCheckResult = {
        available: false,
        message: 'This email is already registered',
        suggestions,
        cached: false,
      };
      this.checkResultCache.set(normalizedEmail, { result, timestamp: Date.now() });
      return result;
    }

    // Success - email is valid and available
    const result: EmailCheckResult = {
      available: true,
      message: 'Email is available',
      cached: false,
    };
    this.checkResultCache.set(normalizedEmail, { result, timestamp: Date.now() });
    return result;
  }

  /**
   * Get email suggestions if email is taken (CONSOLIDATED from duplicate-check service)
   * Suggests alternatives like +farmiq, +farming, .2 suffixes
   */
  async getEmailSuggestions(email: string): Promise<string[]> {
    const [localPart, domain] = email.toLowerCase().split('@');
    if (!domain) return [];

    const suggestions: string[] = [];
    const candidates = [
      `${localPart}+farmiq@${domain}`,           // Add +farmiq
      `${localPart}+farming@${domain}`,          // Add +farming
      `${localPart}.farmer@${domain}`,           // Add .farmer
      `${localPart}2@${domain}`,                 // Add 2
      `${localPart}_farmer@${domain}`,           // Add _farmer
    ];

    // Check each suggestion (max 5)
    for (const suggestion of candidates.slice(0, this.MAX_SUGGESTIONS)) {
      try {
        const available = await this.isEmailAvailable(suggestion);
        if (available) {
          suggestions.push(suggestion);
        }
      } catch (error) {
        console.warn(`Could not check suggestion: ${suggestion}`, error);
      }
    }

    return suggestions;
  }

  /**
   * Validate email format (basic checks)
   * Returns { valid, error, suggestion } for typo detection
   */
  validateEmailFormat(email: string): {
    valid: boolean;
    error?: string;
    suggestion?: string;
  } {
    const normalized = email.trim().toLowerCase();

    // Check for empty
    if (!normalized) {
      return { valid: false, error: 'Email is required' };
    }

    // Check for @ symbol
    if (!normalized.includes('@')) {
      return { valid: false, error: 'Email must contain @' };
    }

    // Check for space or invalid characters
    if (normalized.includes(' ')) {
      return { valid: false, error: 'Email cannot contain spaces' };
    }

    // Check basic email pattern  (RFC 5322 simplified)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(normalized)) {
      return { valid: false, error: 'Please enter a valid email address' };
    }

    // Common typo detection for major domains
    const domain = normalized.split('@')[1];
    const commonTypos: Record<string, string> = {
      'gmial.com': 'gmail.com',
      'gmai.com': 'gmail.com',
      'gmali.com': 'gmail.com',
      'yahooo.com': 'yahoo.com',
      'yaho.com': 'yahoo.com',
      'outlok.com': 'outlook.com',
      'outloo.com': 'outlook.com',
      'hotmial.com': 'hotmail.com',
      'hotmai.com': 'hotmail.com',
      'gmai.co.uk': 'gmail.co.uk',
    };

    if (commonTypos[domain]) {
      const suggestion = email.replace(domain, commonTypos[domain]);
      return {
        valid: true,
        suggestion,
      };
    }

    return { valid: true };
  }

  /**
   * Complete email validation: format + availability (LEGACY METHOD - kept for backward compatibility)
   */
  async validateEmail(email: string): Promise<{
    valid: boolean;
    error?: string;
    suggestion?: string;
    taken?: boolean;
    takeSuggestions?: string[];
  }> {
    const result = await this.checkEmail(email);
    
    if (!result.available) {
      return {
        valid: false,
        taken: true,
        error: result.message,
        takeSuggestions: result.suggestions,
      };
    }

    return { valid: true };
  }

  /**
   * Invalidate cache for email (call after signup success)
   */
  invalidateEmail(email: string): void {
    const normalized = email.toLowerCase().trim();
    this.emailCache.delete(normalized);
    this.checkResultCache.delete(normalized);
    console.log(`🗑️ Invalidated cache for ${email}`);
  }

  /**
   * Clear all cached results
   */
  clearCache(): void {
    this.emailCache.clear();
    this.checkResultCache.clear();
    console.log(`🧹 Cleared email validation cache`);
  }

  /**
   * Internal: Clean up old/expired cache entries
   */
  private cleanupCache(): void {
    const now = Date.now();
    let cleanedCount = 0;

    // Clean simple cache
    for (const [key, value] of this.emailCache.entries()) {
      if (now - value.timestamp > this.EMAIL_CACHE_TTL_MS) {
        this.emailCache.delete(key);
        cleanedCount++;
      }
    }

    // Clean comprehensive result cache
    for (const [key, value] of this.checkResultCache.entries()) {
      if (now - value.timestamp > this.EMAIL_CACHE_TTL_MS) {
        this.checkResultCache.delete(key);
        cleanedCount++;
      }
    }

    if (cleanedCount > 0) {
      console.log(`🧹 Cleaned ${cleanedCount} expired email cache entries`);
    }
  }

  /**
   * Get cache statistics
   */
  getStats(): { simpleCacheSize: number; resultCacheSize: number } {
    return {
      simpleCacheSize: this.emailCache.size,
      resultCacheSize: this.checkResultCache.size,
    };
  }
}
