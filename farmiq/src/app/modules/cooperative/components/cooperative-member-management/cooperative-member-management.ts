import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CooperativeService } from '../../services/cooperative';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-cooperative-member-management',
  imports: [CommonModule, FormsModule],
  templateUrl: './cooperative-member-management.html',
  styleUrl: './cooperative-member-management.scss',
})
export class CooperativeMemberManagementComponent implements OnInit, OnDestroy {
  private cooperativeService = inject(CooperativeService);
  private destroy$ = new Subject<void>();

  members: any[] = [];
  filteredMembers: any[] = [];
  searchTerm = '';
  statusFilter = 'all';
  loading = false;
  error: string | null = null;
  showAddForm = false;
  newMember: any = {
    id: '',
    name: '',
    email: '',
    phone: '',
    joinDate: new Date(),
    status: 'active' as const,
    farmSize: 0,
    creditScore: 0,
  };

  ngOnInit() {
    this.loadMembers();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadMembers() {
    this.loading = true;
    this.error = null;

    this.cooperativeService.getMembers()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.members = data;
          this.filterMembers();
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load members';
          this.loading = false;
        }
      });
  }

  filterMembers() {
    this.filteredMembers = this.members.filter((member) => {
      const matchSearch = member.name.toLowerCase().includes(this.searchTerm.toLowerCase());
      const matchStatus = this.statusFilter === 'all' || member.status === this.statusFilter;
      return matchSearch && matchStatus;
    });
  }

  onSearch() {
    this.filterMembers();
  }

  onStatusFilterChange() {
    this.filterMembers();
  }

  addMember() {
    if (!this.newMember.name || !this.newMember.email) {
      this.error = 'Name and email are required';
      return;
    }

    const memberData = {
      id: '',
      name: this.newMember.name,
      email: this.newMember.email,
      joinDate: new Date(),
      status: 'active' as const,
      farmSize: this.newMember.farmSize || 0,
      creditScore: 0,
    };

    this.cooperativeService.addMember(memberData)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.showAddForm = false;
          this.newMember = { id: '', name: '', email: '', joinDate: new Date(), status: 'active', farmSize: 0, creditScore: 0 };
          this.loadMembers();
        },
        error: (err) => {
          this.error = 'Failed to add member';
        }
      });
  }

  removeMember(memberId: string) {
    if (!confirm('Are you sure?')) return;

    this.cooperativeService.removeMember(memberId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => this.loadMembers(),
        error: (err) => {
          this.error = 'Failed to remove member';
        }
      });
  }

  updateMemberStatus(memberId: string, newStatus: 'active' | 'inactive' | 'suspended') {
    this.cooperativeService.updateMemberStatus(memberId, newStatus)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => this.loadMembers(),
        error: (err) => {
          this.error = 'Failed to update member status';
        }
      });
  }

  getStatusColor(status: string): string {
    const colors: { [key: string]: string } = {
      'active': '#4CAF50',
      'pending': '#FFC107',
      'suspended': '#F44336',
    };
    return colors[status.toLowerCase()] || '#999';
  }
}
