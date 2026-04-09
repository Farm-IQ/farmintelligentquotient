/**
 * Agent Module Models
 * Interfaces for agent-related data
 */

export interface Agent {
  id: string;
  userId: string;
  firstName: string;
  lastName: string;
  email: string;
  phoneNumber: string;
  county: string;
  subCounty?: string;
  registrationDate: Date;
  status: 'active' | 'inactive' | 'suspended' | 'pending_verification';
  verificationStatus: 'pending' | 'verified' | 'rejected';
  walletAddress?: string;
  totalFarmersRegistered: number;
  commissionEarned: number;
  pendingCommission: number;
  withdrawalAccount?: string;
}

export interface AgentWallet {
  id?: string;
  agentId: string;
  balance: number;
  availableBalance: number;
  lockedBalance: number;
  totalEarned: number;
  totalWithdrawn: number;
  lastUpdated: Date;
  currency: 'KES' | 'USD' | 'HBAR';
  walletAddress?: string;
  walletProvider?: 'metamask' | 'hashpack' | 'hedera';
}

export interface AgentVerification {
  id?: string;
  agentId: string;
  idNumber: string;
  idType: 'national_id' | 'passport' | 'driver_license';
  idDocument: string; // URL to uploaded document
  businessRegistration?: string; // URL to business registration
  bankStatement?: string; // URL to bank statement
  verificationDate?: Date;
  verifiedBy?: string;
  status: 'pending' | 'verified' | 'rejected' | 'under_review';
  rejectionReason?: string;
  notes?: string;
}

export interface AgentPerformance {
  agentId: string;
  month: Date;
  farmersRegistered: number;
  totalCommission: number;
  averageScore: number;
  topPerformer: boolean;
  complaints: number;
  rating: number;
}

export interface AgentWithdrawalRequest {
  id?: string;
  agentId: string;
  amount: number;
  status: 'pending' | 'processing' | 'completed' | 'rejected';
  requestDate: Date;
  completionDate?: Date;
  bankAccount: string;
  transactionId?: string;
  notes?: string;
}

export interface AgentCommissionRule {
  id?: string;
  tier: 'bronze' | 'silver' | 'gold' | 'platinum';
  minFarmersRequired: number;
  commissionPercentage: number;
  bonusPercentage?: number;
  effectiveDate: Date;
  endDate?: Date;
  isActive: boolean;
}

export interface AgentRegistrationRequest {
  firstName: string;
  lastName: string;
  email: string;
  phoneNumber: string;
  county: string;
  subCounty?: string;
  idNumber: string;
  idType: 'national_id' | 'passport' | 'driver_license';
  businessRegistration?: string;
  bankAccountNumber: string;
  bankAccountName: string;
}
