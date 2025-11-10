/**
 * Credit Report and Tradeline Types
 * Phase 1: Intake & Credit - Credit Snapshot and Confirmation
 */

export type BureauType = 'equifax' | 'experian' | 'transunion' | 'merged';
export type CreditReportStatus = 'pending' | 'pulled' | 'error' | 'expired';
export type AccountType =
  | 'mortgage'
  | 'auto'
  | 'student'
  | 'credit_card'
  | 'personal'
  | 'installment'
  | 'collection'
  | 'other';
export type AccountStatus = 'open' | 'closed' | 'paid' | 'charge_off' | 'collection';
export type ConfirmationStatus = 'pending' | 'confirmed' | 'disputed';
export type DocTaskType =
  | 'dispute_tradeline'
  | 'verify_tradeline'
  | 'upload_document'
  | 'provide_explanation'
  | 'verify_income'
  | 'verify_assets'
  | 'other';
export type DocTaskStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';

export interface CreditReport {
  id: number;
  user: number;
  loan_estimate: number | null;
  bureau: BureauType;
  status: CreditReportStatus;
  equifax_score: number | null;
  experian_score: number | null;
  transunion_score: number | null;
  report_date: string;
  report_id: string;
  raw_data: Record<string, any>;
  total_tradelines: number;
  total_inquiries: number;
  total_monthly_debt: string;
  error_message: string;
  created_at: string;
  updated_at: string;
  expires_at: string | null;
  middle_score: number | null;
  is_expired: boolean;
  tradelines?: Tradeline[];
}

export interface Tradeline {
  id: number;
  credit_report: number;
  account_type: AccountType;
  creditor_name: string;
  account_number: string;
  current_balance: string;
  monthly_payment: string;
  credit_limit: string | null;
  status: AccountStatus;
  opened_date: string | null;
  last_payment_date: string | null;
  days_past_due: number;
  confirmation_status: ConfirmationStatus;
  confirmed_at: string | null;
  dispute_reason: string;
  raw_data: Record<string, any>;
  created_at: string;
  updated_at: string;
  needs_confirmation: boolean;
}

export interface DocTask {
  id: number;
  user: number;
  loan_estimate: number | null;
  tradeline: number | null;
  task_type: DocTaskType;
  status: DocTaskStatus;
  title: string;
  description: string;
  borrower_notes: string;
  uploaded_documents: number[];
  reviewed_by: number | null;
  admin_notes: string;
  created_at: string;
  due_date: string | null;
  completed_at: string | null;
  updated_at: string;
  is_overdue: boolean;
}

export interface CreditInquiry {
  creditor_name: string;
  inquiry_date: string;
  inquiry_type: 'hard' | 'soft';
}

export interface CreditSnapshot {
  credit_report: CreditReport;
  tradelines: Tradeline[];
  inquiries: CreditInquiry[];
  summary: {
    total_accounts: number;
    open_accounts: number;
    total_balance: string;
    total_monthly_payment: string;
    credit_utilization: number | null;
    derogatory_marks: number;
  };
}

// API Request/Response Types
export interface ConfirmTradelineRequest {
  tradeline_id: number;
  confirmation_status: 'confirmed' | 'disputed';
  dispute_reason?: string;
}

export interface CreateDocTaskRequest {
  tradeline_id?: number;
  loan_estimate_id?: number;
  task_type: DocTaskType;
  title: string;
  description: string;
  due_date?: string;
}

export interface UpdateDocTaskRequest {
  status?: DocTaskStatus;
  borrower_notes?: string;
  uploaded_documents?: number[];
}
