import { Injectable } from '@angular/core';

/**
 * Rate Limit Service
 * Tracks and enforces rate limits for login, signup, and API calls
 * Prevents brute force attacks and API abuse
 */
interface RateLimitRecord {
  count: number;
  resetTime: number;
  warnings: number;
}

@Injectable({
  providedIn: 'root',
})
export class RateLimitService {
  // Rate limit configurations
  private readonly LOGIN_LIMIT = 5;
  private readonly LOGIN_WINDOW_MS = 15 * 60 * 1000; // 15 minutes
  private readonly SIGNUP_LIMIT = 3;
  private readonly SIGNUP_WINDOW_MS = 60 * 60 * 1000; // 1 hour
  private readonly API_CALL_LIMIT = 30;
  private readonly API_CALL_WINDOW_MS = 60 * 1000; // 1 minute

  // In-memory maps for rate limiting
  private loginAttempts = new Map<string, RateLimitRecord>();
  private signupAttempts = new Map<string, RateLimitRecord>();
  private apiCalls = new Map<string, RateLimitRecord>();

  constructor() {
    // Clean up expired entries every 5 minutes
    setInterval(() => this.cleanupExpiredEntries(), 5 * 60 * 1000);
  }

  /**
   * Check if login attempt is allowed for email
   */
  isLoginAllowed(email: string): boolean {
    return this.checkRateLimit(email, this.loginAttempts, this.LOGIN_LIMIT, this.LOGIN_WINDOW_MS);
  }

  /**
   * Record a login attempt (success or failure)
   */
  recordLoginAttempt(email: string, success: boolean = false): void {
    this.recordAttempt(email, this.loginAttempts, this.LOGIN_WINDOW_MS);
    
    if (success) {
      // Clear on successful login
      this.loginAttempts.delete(email);
    }
  }

  /**
   * Get time until next login attempt allowed (milliseconds)
   */
  getLoginRetryTime(email: string): number {
    return this.getRetryTime(email, this.loginAttempts, this.LOGIN_WINDOW_MS);
  }

  /**
   * Check if signup attempt is allowed for email
   */
  isSignupAllowed(email: string): boolean {
    return this.checkRateLimit(email, this.signupAttempts, this.SIGNUP_LIMIT, this.SIGNUP_WINDOW_MS);
  }

  /**
   * Record a signup attempt
   */
  recordSignupAttempt(email: string): void {
    this.recordAttempt(email, this.signupAttempts, this.SIGNUP_WINDOW_MS);
  }

  /**
   * Get time until next signup attempt allowed (milliseconds)
   */
  getSignupRetryTime(email: string): number {
    return this.getRetryTime(email, this.signupAttempts, this.SIGNUP_WINDOW_MS);
  }

  /**
   * Check if API call is allowed from user ID
   */
  isApiCallAllowed(userId: string): boolean {
    return this.checkRateLimit(userId, this.apiCalls, this.API_CALL_LIMIT, this.API_CALL_WINDOW_MS);
  }

  /**
   * Record an API call
   */
  recordApiCall(userId: string): void {
    this.recordAttempt(userId, this.apiCalls, this.API_CALL_WINDOW_MS);
  }

  /**
   * Get current login attempt count
   */
  getLoginAttemptCount(email: string): number {
    const record = this.loginAttempts.get(email);
    return record && record.resetTime > Date.now() ? record.count : 0;
  }

  /**
   * Reset login attempts for email
   */
  resetLoginAttempts(email: string): void {
    this.loginAttempts.delete(email);
  }

  /**
   * Reset signup attempts for email
   */
  resetSignupAttempts(email: string): void {
    this.signupAttempts.delete(email);
  }

  /**
   * Internal: Check rate limit
   */
  private checkRateLimit(
    key: string,
    map: Map<string, RateLimitRecord>,
    limit: number,
    windowMs: number
  ): boolean {
    const now = Date.now();
    const record = map.get(key);

    if (!record || record.resetTime < now) {
      // No record or window expired
      return true;
    }

    // Window still active, check if under limit
    return record.count < limit;
  }

  /**
   * Internal: Record attempt
   */
  private recordAttempt(key: string, map: Map<string, RateLimitRecord>, windowMs: number): void {
    const now = Date.now();
    const existing = map.get(key);

    if (!existing || existing.resetTime < now) {
      // New window or first attempt
      map.set(key, {
        count: 1,
        resetTime: now + windowMs,
        warnings: 0,
      });
    } else {
      // Add to existing window
      existing.count++;
      existing.warnings = Math.max(0, existing.warnings);
      map.set(key, existing);
    }
  }

  /**
   * Internal: Get time until retry allowed
   */
  private getRetryTime(key: string, map: Map<string, RateLimitRecord>, windowMs: number): number {
    const record = map.get(key);
    if (!record) return 0;

    const timeUntilReset = Math.max(0, record.resetTime - Date.now());
    return timeUntilReset;
  }

  /**
   * Internal: Clean up expired entries
   */
  private cleanupExpiredEntries(): void {
    const now = Date.now();
    
    // Clean login attempts
    for (const [key, record] of this.loginAttempts.entries()) {
      if (record.resetTime < now) {
        this.loginAttempts.delete(key);
      }
    }

    // Clean signup attempts
    for (const [key, record] of this.signupAttempts.entries()) {
      if (record.resetTime < now) {
        this.signupAttempts.delete(key);
      }
    }

    // Clean API calls
    for (const [key, record] of this.apiCalls.entries()) {
      if (record.resetTime < now) {
        this.apiCalls.delete(key);
      }
    }
  }

  /**
   * Format milliseconds to human-readable string
   * @example 5000 -> "5s", 60000 -> "1m"
   */
  formatRetryTime(ms: number): string {
    const seconds = Math.ceil(ms / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.ceil(seconds / 60);
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.ceil(minutes / 60);
    return `${hours}h`;
  }
}
