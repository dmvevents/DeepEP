/**
 * Mortgage Status Types
 * Phase 1: Intake & Credit - Mortgage Status Tracking
 */

export type MortgageStatusType =
  | 'forbearance'
  | 'modification'
  | 'transfer'
  | 'foreclosure'
  | null;

export interface MortgageStatus {
  type: MortgageStatusType;
  description?: string;
  startDate?: string;
  endDate?: string;
  notes?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  default_state: number | null;
  default_county: number | null;
  annual_income: string | null;
  credit_score: number | null;
  mortgage_statuses: MortgageStatus[];
  created_at: string;
  updated_at: string;
}
