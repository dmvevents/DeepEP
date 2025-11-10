import axios from 'axios';
import type {
  CreditReport,
  CreditSnapshot,
  Tradeline,
  DocTask,
  ConfirmTradelineRequest,
  CreateDocTaskRequest,
  UpdateDocTaskRequest,
} from '../types/credit';

const PROPERTY_API_BASE = 'http://localhost:8004';
const OCR_API_BASE = 'http://localhost:8003';
const BACKEND_API_BASE = 'http://localhost:8000';

// Create axios instance with auth token support
const apiClient = axios.create({
  baseURL: BACKEND_API_BASE,
});

// Add auth token to requests if available
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface PropertyLookupResponse {
  address: {
    formatted_address: string;
    county: string;
    state: string;
    zip_code: string;
  };
  tax_rate: number;
  monthly_property_tax: number;
  insurance_estimate: number;
  confidence_score: number;
}

export interface TransferTaxCalculation {
  scenario: string;
  transfer_taxes: {
    state: number;
    county: number;
    total: number;
  };
  recording_fees: {
    deed: number;
    mortgage: number;
    surcharges: number;
    total: number;
  };
  recordation_tax: number;
  responsibility_split: {
    buyer_percent: number;
    seller_percent: number;
  };
  costs: {
    buyer: number;
    seller: number;
    total: number;
  };
  exemptions: {
    first_time_buyer_savings: number;
    applied: string[];
  };
}

export interface DocumentExtractionResponse {
  document_id: string;
  extracted_data: any;
  confidence_score: number;
  processing_time: number;
}

// Property API
export const propertyApi = {
  lookup: async (address: string): Promise<PropertyLookupResponse> => {
    const response = await axios.get(`${PROPERTY_API_BASE}/api/property/lookup`, {
      params: { address },
    });
    return response.data;
  },

  calculateTransferTax: async (
    salesPrice: number,
    isNewConstruction: boolean,
    isFirstTimeBuyer: boolean
  ): Promise<TransferTaxCalculation> => {
    const response = await axios.post(`${PROPERTY_API_BASE}/api/property/calculate-transfer-tax`, {
      sales_price: salesPrice,
      is_new_construction: isNewConstruction,
      is_first_time_buyer: isFirstTimeBuyer,
    });
    return response.data;
  },
};

// OCR API
export const ocrApi = {
  extractDocument: async (file: File): Promise<DocumentExtractionResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(`${OCR_API_BASE}/extract`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// Mock qualification calculation (to be replaced with real backend)
export interface QualificationResult {
  qualified: boolean;
  monthly_income: number;
  housing_payment: number;
  back_end_dti: number;
  front_end_dti: number;
  qualified_loan_types: string[];
  warnings: string[];
}

export const calculateQualification = async (data: {
  propertyValue: number;
  loanAmount: number;
  interestRate: number;
  loanTerm: number;
  propertyTax: number;
  insurance: number;
  hoaFees: number;
  monthlyIncome: number;
  carPayments: number;
  studentLoans: number;
  creditCards: number;
  personalLoans: number;
  otherDebts: number;
}): Promise<QualificationResult> => {
  // Calculate monthly mortgage payment (P&I)
  const monthlyRate = data.interestRate / 100 / 12;
  const numPayments = data.loanTerm * 12;
  const monthlyPI =
    (data.loanAmount * monthlyRate * Math.pow(1 + monthlyRate, numPayments)) /
    (Math.pow(1 + monthlyRate, numPayments) - 1);

  // Calculate total housing payment (PITI)
  const housingPayment = monthlyPI + data.propertyTax + data.insurance + data.hoaFees;

  // Calculate total monthly debts
  const totalDebts =
    housingPayment +
    data.carPayments +
    data.studentLoans +
    data.creditCards +
    data.personalLoans +
    data.otherDebts;

  // Calculate DTI ratios
  const frontEndDti = (housingPayment / data.monthlyIncome) * 100;
  const backEndDti = (totalDebts / data.monthlyIncome) * 100;

  // Determine qualification
  const qualifiedLoanTypes: string[] = [];
  const warnings: string[] = [];

  // Fannie Mae: Front-end <= 28%, Back-end <= 36% (standard)
  if (frontEndDti <= 28 && backEndDti <= 36) {
    qualifiedLoanTypes.push('Fannie Mae (Conventional)');
  } else if (frontEndDti <= 33 && backEndDti <= 43) {
    qualifiedLoanTypes.push('Fannie Mae (Expanded Criteria)');
    warnings.push('Requires compensating factors for Fannie Mae');
  }

  // FHA: Front-end <= 31%, Back-end <= 43%
  if (frontEndDti <= 31 && backEndDti <= 43) {
    qualifiedLoanTypes.push('FHA');
  } else if (backEndDti <= 50) {
    qualifiedLoanTypes.push('FHA (Manual Underwriting)');
    warnings.push('Requires manual underwriting for FHA');
  }

  // VA: Back-end <= 41%
  if (backEndDti <= 41) {
    qualifiedLoanTypes.push('VA');
  }

  // DTI warnings
  if (backEndDti > 43 && backEndDti <= 50) {
    warnings.push('High DTI ratio - limited loan options available');
  } else if (backEndDti > 50) {
    warnings.push('DTI ratio exceeds most lender limits');
  }

  return {
    qualified: qualifiedLoanTypes.length > 0,
    monthly_income: data.monthlyIncome,
    housing_payment: housingPayment,
    back_end_dti: backEndDti,
    front_end_dti: frontEndDti,
    qualified_loan_types: qualifiedLoanTypes,
    warnings,
  };
};

// Credit API
export const creditApi = {
  // Get credit snapshot for a loan estimate
  getCreditSnapshot: async (loanEstimateId: number): Promise<CreditSnapshot> => {
    const response = await apiClient.get(`/api/credit/snapshot/${loanEstimateId}/`);
    return response.data;
  },

  // Get credit report by ID
  getCreditReport: async (creditReportId: number): Promise<CreditReport> => {
    const response = await apiClient.get(`/api/credit/reports/${creditReportId}/`);
    return response.data;
  },

  // Pull new credit report for user
  pullCreditReport: async (loanEstimateId: number): Promise<CreditReport> => {
    const response = await apiClient.post(`/api/credit/pull/`, { loan_estimate_id: loanEstimateId });
    return response.data;
  },

  // Confirm or dispute a tradeline
  updateTradelineConfirmation: async (data: ConfirmTradelineRequest): Promise<Tradeline> => {
    const response = await apiClient.patch(`/api/credit/tradelines/${data.tradeline_id}/confirm/`, {
      confirmation_status: data.confirmation_status,
      dispute_reason: data.dispute_reason,
    });
    return response.data;
  },

  // Get tradelines for a credit report
  getTradelines: async (creditReportId: number): Promise<Tradeline[]> => {
    const response = await apiClient.get(`/api/credit/reports/${creditReportId}/tradelines/`);
    return response.data;
  },

  // Create a DocTask
  createDocTask: async (data: CreateDocTaskRequest): Promise<DocTask> => {
    const response = await apiClient.post(`/api/credit/doc-tasks/`, data);
    return response.data;
  },

  // Update a DocTask
  updateDocTask: async (taskId: number, data: UpdateDocTaskRequest): Promise<DocTask> => {
    const response = await apiClient.patch(`/api/credit/doc-tasks/${taskId}/`, data);
    return response.data;
  },

  // Get all doc tasks for the current user
  getDocTasks: async (loanEstimateId?: number): Promise<DocTask[]> => {
    const params = loanEstimateId ? { loan_estimate_id: loanEstimateId } : {};
    const response = await apiClient.get(`/api/credit/doc-tasks/`, { params });
    return response.data;
  },
};
