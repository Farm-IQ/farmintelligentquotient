/**
 * Role Field Validators
 * Custom validators for role-specific signup/profile fields
 */

import { ValidatorFn, AbstractControl, ValidationErrors } from '@angular/forms';

export class RoleFieldValidators {
  /**
   * Farm size validator (0.01 - 10000 acres)
   */
  static farmSizeValidator(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      if (!control.value) return null;

      const value = parseFloat(control.value);
      if (isNaN(value)) {
        return { farmSize: { message: 'Farm size must be a number' } };
      }

      if (value < 0.01) {
        return { farmSize: { message: 'Farm size must be at least 0.01 acres' } };
      }

      if (value > 10000) {
        return { farmSize: { message: 'Farm size cannot exceed 10000 acres' } };
      }

      return null;
    };
  }

  /**
   * Member count validator (minimum 1)
   */
  static memberCountValidator(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      if (!control.value) return null;

      const value = parseInt(control.value, 10);
      if (isNaN(value)) {
        return { memberCount: { message: 'Member count must be a number' } };
      }

      if (value < 1) {
        return { memberCount: { message: 'At least 1 member required' } };
      }

      if (value > 10000) {
        return { memberCount: { message: 'Member count seems unrealistic' } };
      }

      return null;
    };
  }

  /**
   * Years of experience validator (0-80)
   */
  static yearsOfExperienceValidator(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      if (!control.value) return null;

      const value = parseInt(control.value, 10);
      if (isNaN(value)) {
        return { yearsExp: { message: 'Years of experience must be a number' } };
      }

      if (value < 0) {
        return { yearsExp: { message: 'Years of experience cannot be negative' } };
      }

      if (value > 80) {
        return { yearsExp: { message: 'Years of experience cannot exceed 80' } };
      }

      return null;
    };
  }

  /**
   * Cooperative registration number validator
   */
  static cooperativeRegNumberValidator(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      if (!control.value) return null;

      const value = control.value.toString().trim();
      if (!/^[A-Z0-9/\-]+$/.test(value)) {
        return { coopRegNumber: { message: 'Invalid registration number format' } };
      }

      if (value.length < 5) {
        return { coopRegNumber: { message: 'Registration number must be at least 5 characters' } };
      }

      return null;
    };
  }

  /**
   * Phone number validator (Kenya format)
   */
  static kenyaPhoneValidator(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      if (!control.value) return null;

      const value = control.value.toString().trim();
      // Kenya phone: +254 or 0 prefix, 10 digits
      const phoneRegex = /^(\+?254|0)(7|1)[0-9]{8}$/;

      if (!phoneRegex.test(value.replace(/\s/g, ''))) {
        return { phone: { message: 'Please enter a valid Kenya phone number' } };
      }

      return null;
    };
  }
}
