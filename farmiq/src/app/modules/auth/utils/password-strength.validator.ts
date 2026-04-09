/**
 * Password Strength Validator
 * Validates and scores password strength
 */

export interface PasswordStrengthResult {
  strength: number; // 0-5
  label: string; // 'Very Weak' to 'Very Strong'
  isValid: boolean;
  requirements: {
    minLength: boolean;
    hasUppercase: boolean;
    hasLowercase: boolean;
    hasNumber: boolean;
    hasSpecialChar: boolean;
  };
  feedback: string[];
}

export class PasswordStrengthValidator {
  private static readonly MIN_LENGTH = 8;
  private static readonly STRENGTH_LABELS = [
    'Very Weak',
    'Weak',
    'Fair',
    'Good',
    'Strong',
    'Very Strong'
  ] as const;

  /**
   * Validate password strength
   */
  static validate(password: string): PasswordStrengthResult {
    const requirements = {
      minLength: password.length >= this.MIN_LENGTH,
      hasUppercase: /[A-Z]/.test(password),
      hasLowercase: /[a-z]/.test(password),
      hasNumber: /[0-9]/.test(password),
      hasSpecialChar: /[!@#$%^&*()_+=\-\[\]{};':"\\|,.<>?/]/.test(password),
    };

    // Calculate strength score
    let score = 0;
    if (requirements.minLength) score++;
    if (requirements.hasUppercase) score++;
    if (requirements.hasLowercase) score++;
    if (requirements.hasNumber) score++;
    if (requirements.hasSpecialChar) score++;

    // Generate feedback
    const feedback: string[] = [];
    if (!requirements.minLength) feedback.push('At least 8 characters required');
    if (!requirements.hasUppercase) feedback.push('Add uppercase letter (A-Z)');
    if (!requirements.hasLowercase) feedback.push('Add lowercase letter (a-z)');
    if (!requirements.hasNumber) feedback.push('Add number (0-9)');
    if (!requirements.hasSpecialChar) feedback.push('Add special character (!@#$%^&*)');

    return {
      strength: score,
      label: this.STRENGTH_LABELS[score],
      isValid: score >= 3, // 'Fair' or better
      requirements,
      feedback,
    };
  }

  /**
   * Check if password meets minimum requirements
   */
  static isValid(password: string): boolean {
    return this.validate(password).isValid;
  }

  /**
   * Get password strength label
   */
  static getLabel(password: string): string {
    return this.validate(password).label;
  }
}
