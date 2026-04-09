/**
 * Cooperative Module Models
 * Interfaces for cooperative-related data
 */

export interface CooperativeMember {
  id: string;
  name: string;
  email: string;
  phoneNumber?: string;
  joinDate: Date;
  status: 'active' | 'inactive' | 'suspended';
  farmSize: number;
  farmLocation: string;
  primaryCrop: string;
  creditScore?: number;
  lastActivity?: Date;
}

export interface CooperativeData {
  id?: string;
  name: string;
  location: string;
  county: string;
  totalMembers: number;
  totalAcreage: number;
  registrationDate: Date;
  representativeName: string;
  representativeEmail: string;
  representativePhone: string;
  bankAccount?: string;
  status: 'active' | 'inactive' | 'suspended';
}

/**
 * FIXED: Added processedCount property
 * This was causing: "Property 'processedCount' does not exist on type 'BulkScoringResult'"
 */
export interface BulkScoringResult {
  membersScored: number;
  processedCount: number;  // ✅ FIXED: Added missing property
  averageScore: number;
  highRiskMembers: number;
  lowRiskMembers: number;
  timestamp: Date;
  successCount: number;
  failureCount: number;
  duration: number; // in milliseconds
}

export interface CooperativeInsights {
  totalRevenue: number;
  memberRetention: number;
  averageCreditScore: number;
  topCommodities: string[];
  marketTrends: Record<string, number>;
  monthlyGrowth: number;
  riskDistribution: {
    highRisk: number;
    mediumRisk: number;
    lowRisk: number;
  };
}

export interface CooperativeFinance {
  id?: string;
  cooperativeId: string;
  totalFunds: number;
  availableFunds: number;
  reserveFunds: number;
  outstandingLoans: number;
  totalRevenue: number;
  expenses: number;
  lastUpdated: Date;
  period: 'monthly' | 'quarterly' | 'annual';
}

export interface CooperativeMemberRequest {
  firstName: string;
  lastName: string;
  email: string;
  phoneNumber: string;
  farmSize: number;
  farmLocation: string;
  county: string;
  primaryCrop: string;
  farmDescription?: string;
}

export interface CooperativeBulkScoringRequest {
  cooperativeId: string;
  memberIds: string[];
  includeAnalysis: boolean;
  riskThreshold?: number;
}

export interface BulkScoringError {
  memberId: string;
  error: string;
  timestamp: Date;
}

export interface BulkScoringDetailedResult extends BulkScoringResult {
  errors: BulkScoringError[];
  successfulMembers: Array<{
    id: string;
    score: number;
    riskLevel: 'high' | 'medium' | 'low';
  }>;
}
