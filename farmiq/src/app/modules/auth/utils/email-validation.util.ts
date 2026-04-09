/**
 * Email Validation Utility
 * Provides email format validation and typo detection
 */

export interface EmailValidationResult {
  valid: boolean;
  error?: string;
  suggestion?: string;
}

export class EmailValidationUtil {
  private static readonly EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  private static readonly COMMON_TYPOS: Record<string, string> = {
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

  /**
   * Validate email format
   */
  static validateEmail(email: string): EmailValidationResult {
    if (!email) {
      return { valid: false, error: 'Email is required' };
    }

    const normalized = email.trim().toLowerCase();

    // Check for @ symbol
    if (!normalized.includes('@')) {
      return { valid: false, error: 'Email must contain @' };
    }

    // Check for spaces
    if (normalized.includes(' ')) {
      return { valid: false, error: 'Email cannot contain spaces' };
    }

    // Check email pattern
    if (!this.EMAIL_REGEX.test(normalized)) {
      return { valid: false, error: 'Please enter a valid email address' };
    }

    // Check for typos
    const domain = normalized.split('@')[1];
    if (this.COMMON_TYPOS[domain]) {
      const suggestion = email.replace(domain, this.COMMON_TYPOS[domain]);
      return {
        valid: true,
        suggestion,
      };
    }

    return { valid: true };
  }

  /**
   * Check if email contains common typos
   */
  static detectTypo(email: string): string | null {
    const normalized = email.toLowerCase();
    const domain = normalized.split('@')[1];
    return this.COMMON_TYPOS[domain] || null;
  }

  /**
   * Normalize email
   */
  static normalize(email: string): string {
    return email.trim().toLowerCase();
  }
}
