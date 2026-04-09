import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminService } from '../../services/admin';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-admin-user-management',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-user-management.html',
  styleUrl: './admin-user-management.scss',
})
export class AdminUserManagementComponent implements OnInit, OnDestroy {
  private adminService = inject(AdminService);
  private destroy$ = new Subject<void>();

  users: any[] = [];
  filteredUsers: any[] = [];
  selectedUser: any = null;
  loading = false;
  error = '';
  successMessage = '';

  filterRole = 'all';
  searchQuery = '';
  showUserForm = false;

  newUser: any = {
    email: '',
    fullName: '',
    phone: '',
    role: 'farmer',
    status: 'active'
  };

  ngOnInit() {
    this.loadUsers();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadUsers() {
    this.loading = true;
    this.adminService.getAllUsers()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (users) => {
          this.users = users;
          this.applyFilters();
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load users';
          this.loading = false;
        }
      });
  }

  applyFilters() {
    this.filteredUsers = this.users.filter(user => {
      const matchesRole = this.filterRole === 'all' || user.role === this.filterRole;
      const matchesSearch = user.fullName.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        user.email.toLowerCase().includes(this.searchQuery.toLowerCase());
      return matchesRole && matchesSearch;
    });
  }

  onSearch() {
    this.applyFilters();
  }

  onRoleFilterChange() {
    this.applyFilters();
  }

  selectUser(user: any) {
    this.selectedUser = user;
  }

  assignRole(userId: string, newRole: string) {
    this.adminService.assignRole(userId, newRole)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.successMessage = 'Role assigned successfully';
          this.loadUsers();
        },
        error: (err) => this.error = 'Failed to assign role'
      });
  }

  suspendUser(userId: string) {
    this.adminService.suspendUser(userId, 'Administrative suspension')
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.successMessage = 'User suspended';
          this.loadUsers();
        },
        error: (err) => this.error = 'Failed to suspend user'
      });
  }

  reactivateUser(userId: string) {
    this.adminService.reactivateUser(userId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.successMessage = 'User reactivated';
          this.loadUsers();
        },
        error: (err) => this.error = 'Failed to reactivate user'
      });
  }

  getStatusColor(status: string): string {
    if (status === 'active') return '#4CAF50';
    if (status === 'suspended') return '#FFC107';
    return '#f44336';
  }

  getRoleColor(role: string): string {
    const colors: any = {
      farmer: '#667eea',
      cooperative: '#764ba2',
      lender: '#FF6B6B',
      agent: '#4ECDC4',
      admin: '#95E1D3'
    };
    return colors[role] || '#999';
  }
}
