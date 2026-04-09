/**
 * OAuth Role Selection Modal with Role-Specific Forms
 * 
 * Displays after OAuth login to let users select their role and fill role-specific data
 * Includes inline form fields that change based on selected role
 * Mirrors the signup component form structure for consistency
 */

import { Component, Input, Output, EventEmitter, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { SupabaseService } from '../../../services/supabase';
import { AuthRoleService, UserRole } from '../../../services/auth-role';
import type { UserRoleType } from '../../../models';

export interface RoleSelectionResult {
  success: boolean;
  role: UserRole;
  message: string;
  error?: string;
}

@Component({
  selector: 'app-oauth-role-selection-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './oauth-role-selection-modal.html',
  styleUrl: './oauth-role-selection-modal.scss',
})
export class OAuthRoleSelectionModalComponent implements OnInit {
  @Input() isVisible = false;
  @Input() provider: 'google' | 'github' = 'google';
  @Input() userEmail = '';
  @Output() roleSelected = new EventEmitter<RoleSelectionResult>();
  @Output() closed = new EventEmitter<void>();

  selectedRole: UserRole | null = null;
  isLoading = false;
  error = '';
  showFormSection = false;

  roleForm!: FormGroup;
  currentStep: 'role-selection' | 'form-completion' = 'role-selection';

  // Map role names to form group keys
  private roleFieldsMap: { [key in UserRole]: string } = {
    farmer: 'farmerFields',
    cooperative: 'cooperativeFields',
    agent: 'agentFields',
    vendor: 'vendorFields',
    lender: 'lenderFields',
    worker: 'workerFields',
    admin: 'adminFields',
  };

  // Role information with descriptions and icons
  // UPDATED: Removed 'worker' role (workers are added by farmers)
  roleOptions: Array<{ role: UserRole; label: string; description: string; icon: string }> = [
    {
      role: 'farmer' as UserRole,
      label: 'Farmer',
      description: 'Individual farmer managing a farm',
      icon: '🌾',
    },
    {
      role: 'cooperative' as UserRole,
      label: 'Cooperative',
      description: 'Farmer cooperative or group',
      icon: '👥',
    },
    {
      role: 'lender' as UserRole,
      label: 'Lender',
      description: 'Microfinance or lending institution',
      icon: '🏦',
    },
    {
      role: 'agent' as UserRole,
      label: 'Agent',
      description: 'Agricultural extension agent',
      icon: '📋',
    },
    {
      role: 'vendor' as UserRole,
      label: 'Vendor',
      description: 'Agricultural input supplier',
      icon: '🛒',
    },
  ];

  // Kenya counties for location selectors
  kenyanCounties: string[] = [
    'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika', 'Naivasha', 'Kitale', 'Machakos', 'Garissa',
    'Meru', 'Embu', 'Nyeri', 'Nanyuki', 'Nairobi City', 'Kajiado', 'Narok', 'Baringo', 'Laikipia', 'Uasin Gishu',
    'Kilifi', 'Kwale', 'Taita-Taveta', 'Machakos', 'Makueni', 'Kitui', 'Meru', 'Tharaka-Nithi', 'Isiolo', 'Samburu',
    'West Pokot', 'Elgeyo-Marakwet', 'Bomet', 'Kericho', 'Homabay', 'Migori', 'Siaya', 'Busia', 'Vihiga', 'Kakamega',
    'Bungoma', 'Trans-Nzoia', 'Turkana', 'Wajir', 'Mandera', 'Marsabit', 'Tana River', 'Lamu', 'Kwale'
  ];

  constructor(
    private formBuilder: FormBuilder,
    private supabase: SupabaseService,
    private authRole: AuthRoleService,
    private router: Router
  ) {
    this.initializeForm();
  }

  ngOnInit(): void {
    // Reset state when visibility changes
    if (!this.isVisible) {
      this.selectedRole = null;
      this.error = '';
      this.currentStep = 'role-selection';
      this.showFormSection = false;
    }
  }

  /**
   * Initialize empty form with all role-specific groups
   */
  private initializeForm(): void {
    this.roleForm = this.formBuilder.group({
      // Farmer-specific fields - SIMPLIFIED
      // Farm setup details are handled by farm setup wizard
      farmerFields: this.formBuilder.group({
        county: ['', Validators.required],
        location: ['', Validators.required],
      }),

      // Cooperative-specific fields
      cooperativeFields: this.formBuilder.group({
        cooperativeName: ['', Validators.maxLength(100)],
        cooperativeType: ['Primary'],
        registrationNumber: [''],
        registrationDate: [''],
        tinNumber: [''],
        cicNumber: [''],
        county: [''],
        location: [''],
        principalOfficerName: [''],
        chairpersonName: [''],
        treasurerName: [''],
        memberCount: ['', [Validators.min(1)]],
        primaryCommodity: [''],
        cacNumber: [''],
        pin: [''],
      }),

      // Agent-specific fields
      agentFields: this.formBuilder.group({
        agentNumber: [''],
        agentType: ['Field Agent'],
        county: [''],
        location: [''],
        yearsOfExperience: ['', [Validators.min(0)]],
        specialization: [''],
        coveredFarmers: ['', [Validators.min(1)]],
        languagesSpoken: [''],
        certifications: [''],
      }),

      // Vendor-specific fields
      vendorFields: this.formBuilder.group({
        vendorName: ['', Validators.maxLength(100)],
        vendorType: ['input_supplier'],
        businessRegistrationNumber: [''],
        businessRegistrationDate: [''],
        county: [''],
        location: [''],
        businessDescription: ['', Validators.maxLength(500)],
        yearsInBusiness: ['', [Validators.min(0)]],
        primaryProduct: [''],
        secondaryProducts: [''],
        serviceArea: [''],
        businessOwnerName: [''],
        businessOwnerPhone: [''],
        businessOwnerEmail: [''],
        tin: [''],
        businessLicense: [''],
      }),

      // Lender-specific fields
      lenderFields: this.formBuilder.group({
        institutionName: ['', Validators.maxLength(100)],
        institutionType: [''],
        registrationNumber: [''],
        licenseNumber: [''],
        cbkCode: [''],
        county: [''],
        location: [''],
        principalOfficerName: [''],
        principalOfficerPhone: [''],
        principalOfficerEmail: [''],
        tin: [''],
        minLoanAmount: ['', [Validators.min(0)]],
        maxLoanAmount: ['', [Validators.min(0)]],
        interestRate: ['', [Validators.min(0), Validators.max(100)]],
        loanProcessingFee: [''],
        loanTenureMonths: ['', [Validators.min(1)]],
      }),

      // Admin-specific fields (minimal for admin users)
      adminFields: this.formBuilder.group({
        departmentName: [''],
        adminLevel: [''],
      }),
    });
  }

  /**
   * Select a role and move to form completion step
   */
  selectRole(role: UserRole): void {
    this.selectedRole = role;
    this.currentStep = 'form-completion';
    this.showFormSection = true;
    this.error = '';

    // Update form validators based on selected role
    this.updateFormValidators(role);
  }

  /**
   * Update form validators for selected role
   */
  private updateFormValidators(role: UserRole): void {
    // Remove all validators first
    this.clearAllValidators();

    // Add role-specific required validators
    const roleFieldsGroup = this.roleForm.get(this.roleFieldsMap[role]) as FormGroup;
    if (roleFieldsGroup) {
      this.setRoleValidators(role, roleFieldsGroup);
    }

    this.roleForm.updateValueAndValidity();
  }

  /**
   * Set validators for specific role fields
   */
  private setRoleValidators(role: UserRole, formGroup: FormGroup): void {
    switch (role) {
      case 'farmer':
        this.setFieldRequired(formGroup, [
          'county',
          'location',
        ]);
        break;
      case 'cooperative':
        this.setFieldRequired(formGroup, [
          'cooperativeName',
          'cooperativeType',
          'registrationNumber',
          'tinNumber',
          'county',
          'location',
          'principalOfficerName',
          'memberCount',
          'primaryCommodity',
        ]);
        break;
      case 'agent':
        this.setFieldRequired(formGroup, [
          'agentNumber',
          'agentType',
          'county',
          'location',
          'yearsOfExperience',
          'specialization',
          'coveredFarmers',
        ]);
        break;
      case 'vendor':
        this.setFieldRequired(formGroup, [
          'vendorName',
          'vendorType',
          'businessRegistrationNumber',
          'county',
          'location',
          'businessDescription',
          'yearsInBusiness',
          'primaryProduct',
          'businessOwnerName',
        ]);
        break;
      case 'lender':
        this.setFieldRequired(formGroup, [
          'institutionName',
          'institutionType',
          'registrationNumber',
          'licenseNumber',
          'county',
          'location',
          'principalOfficerName',
          'tin',
          'minLoanAmount',
          'maxLoanAmount',
          'interestRate',
          'loanTenureMonths',
        ]);
        break;

      case 'admin':
        // Admin fields are typically not required in OAuth flow
        break;
    }
  }

  /**
   * Helper to mark fields as required
   */
  private setFieldRequired(formGroup: FormGroup, fieldNames: string[]): void {
    fieldNames.forEach(fieldName => {
      const control = formGroup.get(fieldName);
      if (control) {
        control.setValidators([Validators.required, ...control.validator ? [control.validator] : []]);
        control.updateValueAndValidity({ emitEvent: false });
      }
    });
  }

  /**
   * Clear all validators
   */
  private clearAllValidators(): void {
    Object.keys(this.roleForm.controls).forEach(key => {
      const control = this.roleForm.get(key);
      if (control instanceof FormGroup) {
        Object.keys(control.controls).forEach(fieldKey => {
          const field = control.get(fieldKey);
          if (field) {
            field.clearValidators();
            field.updateValueAndValidity({ emitEvent: false });
          }
        });
      }
    });
  }

  /**
   * Go back to role selection
   */
  goBack(): void {
    this.currentStep = 'role-selection';
    this.showFormSection = false;
    this.error = '';
  }

  /**
   * Submit form with role-specific data
   */
  async submitForm(): Promise<void> {
    if (!this.selectedRole) {
      this.error = 'Please select a role';
      return;
    }

    const roleFormGroup = this.roleForm.get(this.roleFieldsMap[this.selectedRole]) as FormGroup;

    if (roleFormGroup && roleFormGroup.invalid) {
      this.error = 'Please fill in all required fields';
      return;
    }

    this.isLoading = true;
    this.error = '';

    try {
      let session = await this.supabase.getSession();

      if (!session) {
        const { data, error } = await (this.supabase as any).getClient().auth.getSession();
        if (error || !data.session) {
          throw new Error('No active session found. Please sign in again.');
        }
        session = data.session;
      }

      if (!session?.user?.id) {
        throw new Error('No active session found. Please sign in again.');
      }

      const user = session.user;

      console.log(`📞 Assigning role for user:`, {
        userId: user.id,
        email: user.email,
        role: this.selectedRole,
        provider: this.provider,
      });

      // Assign role to user
      await this.supabase.assignRoleToUser(user.id, this.selectedRole as any);

      // Update user profile with primary role
      await this.supabase.updateUserPrimaryRole(user.id, this.selectedRole);

      // Store role-specific data (optional - can be extended to save to specific tables)
      console.log(`✅ Role "${this.selectedRole}" assigned to user ${user.id}`);
      console.log('Role-specific data:', roleFormGroup.value);

      const resultData: RoleSelectionResult = {
        success: true,
        role: this.selectedRole,
        message: `Role "${this.selectedRole}" assigned successfully!`,
      };

      this.roleSelected.emit(resultData);

      // Navigate to role-specific dashboard
      setTimeout(() => {
        this.authRole.navigateToRoleDashboard(this.selectedRole as UserRoleType);
      }, 1000);
    } catch (error: any) {
      console.error('Error assigning role:', error);
      this.error = error.message || 'Failed to assign role. Please try again.';

      const resultData: RoleSelectionResult = {
        success: false,
        role: this.selectedRole,
        message: 'Failed to assign role',
        error: this.error,
      };

      this.roleSelected.emit(resultData);
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * Close modal without selecting role
   */
  closeModal(): void {
    this.selectedRole = null;
    this.error = '';
    this.currentStep = 'role-selection';
    this.showFormSection = false;
    this.closed.emit();
  }

  /**
   * Check if role is selected
   */
  isRoleSelected(role: UserRole): boolean {
    return this.selectedRole === role;
  }

  /**
   * Get role label for display
   */
  getRoleLabel(role: UserRole): string {
    const roleOption = this.roleOptions.find(r => r.role === role);
    return roleOption?.label || role;
  }

  /**
   * Get form group for current role
   */
  getCurrentRoleFormGroup(): FormGroup | null {
    if (!this.selectedRole) return null;
    return this.roleForm.get(this.roleFieldsMap[this.selectedRole]) as FormGroup;
  }
}
