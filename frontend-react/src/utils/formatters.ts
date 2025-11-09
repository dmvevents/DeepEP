/**
 * Utility functions for formatting currency, dates, phone numbers, etc.
 * Uses date-fns for dates and includes validation helpers.
 */

import { format, formatDistanceToNow, parseISO } from 'date-fns';

/**
 * Format number as US currency
 * @param amount - Number to format
 * @param includeDecimals - Whether to show cents (default: false)
 * @returns Formatted currency string (e.g., "$400,000" or "$1,234.56")
 */
export const formatCurrency = (amount: number | string, includeDecimals: boolean = false): string => {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;

  if (isNaN(num)) return '$0';

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: includeDecimals ? 2 : 0,
    maximumFractionDigits: includeDecimals ? 2 : 0,
  }).format(num);
};

/**
 * Format number with commas (no currency symbol)
 * @param num - Number to format
 * @returns Formatted number string (e.g., "1,234,567")
 */
export const formatNumber = (num: number | string): string => {
  const n = typeof num === 'string' ? parseFloat(num) : num;

  if (isNaN(n)) return '0';

  return new Intl.NumberFormat('en-US').format(n);
};

/**
 * Format percentage
 * @param value - Number to format as percentage
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted percentage string (e.g., "28.50%")
 */
export const formatPercentage = (value: number, decimals: number = 2): string => {
  return `${value.toFixed(decimals)}%`;
};

/**
 * Format phone number as (XXX) XXX-XXXX
 * @param phone - Phone number string (10 digits)
 * @returns Formatted phone number
 */
export const formatPhoneNumber = (phone: string): string => {
  // Remove all non-digit characters
  const cleaned = phone.replace(/\D/g, '');

  // Format as (XXX) XXX-XXXX
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  }

  // Return as-is if not 10 digits
  return phone;
};

/**
 * Format SSN with masking (XXX-XX-1234)
 * @param ssn - Social Security Number
 * @param fullyMask - If true, show only last 4 digits (default: true)
 * @returns Formatted SSN
 */
export const formatSSN = (ssn: string, fullyMask: boolean = true): string => {
  const cleaned = ssn.replace(/\D/g, '');

  if (cleaned.length !== 9) return ssn;

  if (fullyMask) {
    return `XXX-XX-${cleaned.slice(5)}`;
  }

  return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 5)}-${cleaned.slice(5)}`;
};

/**
 * Format date as "Nov 8, 2025"
 * @param date - Date string or Date object
 * @returns Formatted date string
 */
export const formatDate = (date: string | Date): string => {
  try {
    const d = typeof date === 'string' ? parseISO(date) : date;
    return format(d, 'MMM d, yyyy');
  } catch {
    return 'Invalid date';
  }
};

/**
 * Format date with time as "Nov 8, 2025 at 2:30 PM"
 * @param date - Date string or Date object
 * @returns Formatted date and time string
 */
export const formatDateTime = (date: string | Date): string => {
  try {
    const d = typeof date === 'string' ? parseISO(date) : date;
    return format(d, 'MMM d, yyyy \'at\' h:mm a');
  } catch {
    return 'Invalid date';
  }
};

/**
 * Format date as relative time ("2 hours ago", "3 days ago")
 * @param date - Date string or Date object
 * @returns Relative time string
 */
export const formatRelativeTime = (date: string | Date): string => {
  try {
    const d = typeof date === 'string' ? parseISO(date) : date;
    return formatDistanceToNow(d, { addSuffix: true });
  } catch {
    return 'Invalid date';
  }
};

/**
 * Format date for closing date (user-friendly format)
 * @param date - Date string or Date object
 * @returns Formatted closing date (e.g., "Friday, June 15, 2025")
 */
export const formatClosingDate = (date: string | Date): string => {
  try {
    const d = typeof date === 'string' ? parseISO(date) : date;
    return format(d, 'EEEE, MMMM d, yyyy');
  } catch {
    return 'Invalid date';
  }
};

/**
 * Parse currency input (removes $ and commas)
 * @param value - Currency string like "$400,000"
 * @returns Numeric value
 */
export const parseCurrency = (value: string): number => {
  const cleaned = value.replace(/[$,]/g, '');
  const num = parseFloat(cleaned);
  return isNaN(num) ? 0 : num;
};

/**
 * Format address for display
 * @param address - Address components
 * @returns Formatted address string
 */
export const formatAddress = (address: {
  street?: string;
  city?: string;
  state?: string;
  zip?: string;
}): string => {
  const parts = [
    address.street,
    address.city,
    address.state && address.zip ? `${address.state} ${address.zip}` : address.state || address.zip,
  ].filter(Boolean);

  return parts.join(', ');
};

/**
 * Truncate text with ellipsis
 * @param text - Text to truncate
 * @param maxLength - Maximum length before truncation
 * @returns Truncated text
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
};

/**
 * Format file size in human-readable format
 * @param bytes - File size in bytes
 * @returns Formatted file size (e.g., "2.5 MB")
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Format loan term (years to "30 years" or "15 years")
 * @param years - Number of years
 * @returns Formatted loan term
 */
export const formatLoanTerm = (years: number): string => {
  return `${years} ${years === 1 ? 'year' : 'years'}`;
};

/**
 * Format interest rate (e.g., "6.5%" or "6.500%")
 * @param rate - Interest rate as decimal
 * @param decimals - Number of decimal places (default: 3)
 * @returns Formatted interest rate
 */
export const formatInterestRate = (rate: number, decimals: number = 3): string => {
  return `${rate.toFixed(decimals)}%`;
};

/**
 * Format loan-to-value ratio
 * @param loanAmount - Loan amount
 * @param propertyValue - Property value
 * @returns Formatted LTV ratio (e.g., "80%")
 */
export const formatLTV = (loanAmount: number, propertyValue: number): string => {
  if (propertyValue === 0) return '0%';
  const ltv = (loanAmount / propertyValue) * 100;
  return `${ltv.toFixed(0)}%`;
};

/**
 * Format DTI ratio with color coding hint
 * @param dti - DTI percentage
 * @returns Object with formatted DTI and risk level
 */
export const formatDTI = (dti: number): { formatted: string; risk: 'low' | 'medium' | 'high' } => {
  let risk: 'low' | 'medium' | 'high' = 'low';

  if (dti > 43) risk = 'high';
  else if (dti > 36) risk = 'medium';

  return {
    formatted: `${dti.toFixed(2)}%`,
    risk,
  };
};

/**
 * Validate email format
 * @param email - Email address to validate
 * @returns True if valid email format
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate phone number (10 digits)
 * @param phone - Phone number to validate
 * @returns True if valid phone number
 */
export const isValidPhone = (phone: string): boolean => {
  const cleaned = phone.replace(/\D/g, '');
  return cleaned.length === 10;
};

/**
 * Validate SSN (9 digits)
 * @param ssn - SSN to validate
 * @returns True if valid SSN format
 */
export const isValidSSN = (ssn: string): boolean => {
  const cleaned = ssn.replace(/\D/g, '');
  return cleaned.length === 9;
};

/**
 * Validate ZIP code (5 or 9 digits)
 * @param zip - ZIP code to validate
 * @returns True if valid ZIP code
 */
export const isValidZipCode = (zip: string): boolean => {
  const cleaned = zip.replace(/\D/g, '');
  return cleaned.length === 5 || cleaned.length === 9;
};

/**
 * Get initials from full name
 * @param name - Full name
 * @returns Initials (e.g., "JD" from "John Doe")
 */
export const getInitials = (name: string): string => {
  if (!name) return 'U';
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
  }
  return parts[0][0].toUpperCase();
};

/**
 * Format application status with proper casing
 * @param status - Status string from backend
 * @returns Formatted status (e.g., "needs_correction" → "Needs Correction")
 */
export const formatStatus = (status: string): string => {
  return status
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};
