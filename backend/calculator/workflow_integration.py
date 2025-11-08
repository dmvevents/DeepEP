"""
Mortgage Qualification Workflow Integration

End-to-end integration that connects:
1. OCR Document Extraction
2. Income Qualification Engine
3. DTI Calculation
4. Multi-Guideline Qualification Assessment

Created by: Neumann Rashid AI Development
Date: November 8, 2025
"""

import requests
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .income_engine import IncomeQualificationEngine
from .dti_calculator import DTICalculator


class MortgageQualificationWorkflow:
    """
    Complete mortgage qualification workflow.

    Orchestrates document extraction, income calculation, DTI analysis,
    and qualification decision across multiple loan types.
    """

    def __init__(
        self,
        ocr_service_url: str = "http://localhost:8003",
        tax_scraper_url: str = "http://localhost:8001",
    ):
        """
        Initialize workflow with service URLs.

        Args:
            ocr_service_url: URL for OCR extraction service
            tax_scraper_url: URL for tax data scraper service
        """
        self.ocr_service_url = ocr_service_url
        self.tax_scraper_url = tax_scraper_url

    def extract_document(
        self,
        file_path: str,
        document_type: str
    ) -> Dict:
        """
        Extract data from document using OCR service.

        Args:
            file_path: Path to document file
            document_type: Type of document (paystub, w2, bank_statement, etc.)

        Returns:
            Dict with extracted data and metadata
        """
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.ocr_service_url}/extract/{document_type}",
                files=files,
                timeout=60
            )
            response.raise_for_status()
            return response.json()

    def calculate_income_from_documents(
        self,
        loan_type: str,
        loan_amount: Decimal,
        property_value: Decimal,
        paystub_files: Optional[List[str]] = None,
        w2_files: Optional[List[str]] = None,
        tax_return_files: Optional[List[str]] = None,
        bank_statement_files: Optional[List[str]] = None,
    ) -> Dict:
        """
        Extract documents and calculate qualifying income.

        Args:
            loan_type: Loan type (fannie_mae, fha, va)
            loan_amount: Loan amount
            property_value: Property value
            paystub_files: List of paystub file paths
            w2_files: List of W-2 file paths
            tax_return_files: List of tax return file paths
            bank_statement_files: List of bank statement file paths

        Returns:
            Dict with income calculation results and extraction metadata
        """
        # Extract all documents
        extracted_docs = {
            'paystubs': [],
            'w2s': [],
            'tax_returns': [],
            'bank_statements': [],
        }

        extraction_metadata = {
            'total_documents': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'average_confidence': 0.0,
            'extraction_details': [],
        }

        # Extract paystubs
        if paystub_files:
            for file_path in paystub_files:
                try:
                    result = self.extract_document(file_path, 'paystub')
                    extracted_docs['paystubs'].append(result['extracted_data'])
                    extraction_metadata['total_documents'] += 1
                    extraction_metadata['successful_extractions'] += 1
                    extraction_metadata['extraction_details'].append({
                        'file': file_path,
                        'type': 'paystub',
                        'confidence': result['confidence_score'],
                        'success': True,
                    })
                except Exception as e:
                    extraction_metadata['total_documents'] += 1
                    extraction_metadata['failed_extractions'] += 1
                    extraction_metadata['extraction_details'].append({
                        'file': file_path,
                        'type': 'paystub',
                        'success': False,
                        'error': str(e),
                    })

        # Extract W-2s
        if w2_files:
            for file_path in w2_files:
                try:
                    result = self.extract_document(file_path, 'w2')
                    extracted_docs['w2s'].append(result['extracted_data'])
                    extraction_metadata['total_documents'] += 1
                    extraction_metadata['successful_extractions'] += 1
                    extraction_metadata['extraction_details'].append({
                        'file': file_path,
                        'type': 'w2',
                        'confidence': result['confidence_score'],
                        'success': True,
                    })
                except Exception as e:
                    extraction_metadata['total_documents'] += 1
                    extraction_metadata['failed_extractions'] += 1
                    extraction_metadata['extraction_details'].append({
                        'file': file_path,
                        'type': 'w2',
                        'success': False,
                        'error': str(e),
                    })

        # Extract tax returns
        if tax_return_files:
            for file_path in tax_return_files:
                try:
                    result = self.extract_document(file_path, 'tax-return')
                    extracted_docs['tax_returns'].append(result['extracted_data'])
                    extraction_metadata['total_documents'] += 1
                    extraction_metadata['successful_extractions'] += 1
                    extraction_metadata['extraction_details'].append({
                        'file': file_path,
                        'type': 'tax_return',
                        'confidence': result['confidence_score'],
                        'success': True,
                    })
                except Exception as e:
                    extraction_metadata['total_documents'] += 1
                    extraction_metadata['failed_extractions'] += 1
                    extraction_metadata['extraction_details'].append({
                        'file': file_path,
                        'type': 'tax_return',
                        'success': False,
                        'error': str(e),
                    })

        # Extract bank statements
        if bank_statement_files:
            for file_path in bank_statement_files:
                try:
                    result = self.extract_document(file_path, 'bank-statement')
                    extracted_docs['bank_statements'].append(result['extracted_data'])
                    extraction_metadata['total_documents'] += 1
                    extraction_metadata['successful_extractions'] += 1
                    extraction_metadata['extraction_details'].append({
                        'file': file_path,
                        'type': 'bank_statement',
                        'confidence': result['confidence_score'],
                        'success': True,
                    })
                except Exception as e:
                    extraction_metadata['total_documents'] += 1
                    extraction_metadata['failed_extractions'] += 1
                    extraction_metadata['extraction_details'].append({
                        'file': file_path,
                        'type': 'bank_statement',
                        'success': False,
                        'error': str(e),
                    })

        # Calculate average confidence
        confidences = [
            detail['confidence']
            for detail in extraction_metadata['extraction_details']
            if detail['success'] and 'confidence' in detail
        ]
        if confidences:
            extraction_metadata['average_confidence'] = sum(confidences) / len(confidences)

        # Initialize income engine
        engine = IncomeQualificationEngine(
            loan_type=loan_type,
            loan_amount=loan_amount,
            property_value=property_value
        )

        # Calculate qualifying income
        income_result = engine.calculate_qualifying_income(
            w2_documents=extracted_docs['w2s'] if extracted_docs['w2s'] else None,
            paystub_documents=extracted_docs['paystubs'] if extracted_docs['paystubs'] else None,
            tax_return_documents=extracted_docs['tax_returns'] if extracted_docs['tax_returns'] else None,
            bank_statement_documents=extracted_docs['bank_statements'] if extracted_docs['bank_statements'] else None,
        )

        return {
            'income_calculation': income_result,
            'extracted_documents': extracted_docs,
            'extraction_metadata': extraction_metadata,
        }

    def complete_qualification_workflow(
        self,
        # Loan details
        loan_type: str,
        loan_amount: Decimal,
        property_value: Decimal,
        interest_rate: Decimal,
        loan_term_years: int,

        # Borrower details
        credit_score: int,

        # Documents
        paystub_files: Optional[List[str]] = None,
        w2_files: Optional[List[str]] = None,
        tax_return_files: Optional[List[str]] = None,
        bank_statement_files: Optional[List[str]] = None,

        # Property costs (monthly)
        property_tax_monthly: Optional[Decimal] = None,
        insurance_monthly: Optional[Decimal] = None,
        hoa_fees_monthly: Decimal = Decimal('0'),

        # Other debts (monthly)
        car_payments: Decimal = Decimal('0'),
        student_loans: Decimal = Decimal('0'),
        credit_card_payments: Decimal = Decimal('0'),
        personal_loans: Decimal = Decimal('0'),
        other_debts: Decimal = Decimal('0'),

        # Additional params
        compensating_factors: Optional[List[str]] = None,
    ) -> Dict:
        """
        Complete end-to-end qualification workflow.

        Args:
            loan_type: Loan type (fannie_mae, fha, va)
            loan_amount: Loan amount
            property_value: Property purchase price
            interest_rate: Annual interest rate (e.g., 6.5 for 6.5%)
            loan_term_years: Loan term in years (typically 30)
            credit_score: Borrower's credit score
            paystub_files: Paystub file paths for OCR
            w2_files: W-2 file paths for OCR
            tax_return_files: Tax return file paths for OCR
            bank_statement_files: Bank statement file paths for OCR
            property_tax_monthly: Monthly property tax (if known)
            insurance_monthly: Monthly insurance (if known)
            hoa_fees_monthly: Monthly HOA fees
            car_payments: Monthly car payments
            student_loans: Monthly student loan payments
            credit_card_payments: Monthly credit card minimum payments
            personal_loans: Monthly personal loan payments
            other_debts: Other monthly debt obligations
            compensating_factors: List of compensating factors

        Returns:
            Complete qualification analysis with decision
        """
        if compensating_factors is None:
            compensating_factors = []

        # Step 1: Extract documents and calculate income
        income_data = self.calculate_income_from_documents(
            loan_type=loan_type,
            loan_amount=loan_amount,
            property_value=property_value,
            paystub_files=paystub_files,
            w2_files=w2_files,
            tax_return_files=tax_return_files,
            bank_statement_files=bank_statement_files,
        )

        monthly_gross_income = Decimal(
            str(income_data['income_calculation']['monthly_qualifying_income'])
        )

        # Step 2: Calculate monthly P&I payment
        monthly_rate = (interest_rate / 100) / 12
        num_payments = loan_term_years * 12

        if monthly_rate == 0:
            principal_interest = loan_amount / num_payments
        else:
            principal_interest = loan_amount * (
                monthly_rate * ((1 + monthly_rate) ** num_payments)
            ) / (
                ((1 + monthly_rate) ** num_payments) - 1
            )

        # Calculate mortgage insurance if needed
        down_payment = property_value - loan_amount
        down_payment_pct = (down_payment / property_value * 100)
        ltv = (loan_amount / property_value * 100)

        mortgage_insurance = Decimal('0')
        if ltv > 80:
            # Conventional: PMI (~0.5-1% annually, divided by 12)
            if loan_type in ['fannie_mae', 'conventional']:
                pmi_rate = Decimal('0.005')  # 0.5% annually
                mortgage_insurance = (loan_amount * pmi_rate) / 12
            # FHA: MIP (0.85% annually for most loans)
            elif loan_type in ['fha', 'government']:
                mip_rate = Decimal('0.0085')
                mortgage_insurance = (loan_amount * mip_rate) / 12
            # VA: No mortgage insurance (funding fee is upfront)

        # Use provided property tax/insurance or estimate
        if property_tax_monthly is None:
            # Estimate: 1.2% annually / 12
            property_tax_monthly = (property_value * Decimal('0.012')) / 12

        if insurance_monthly is None:
            # Estimate: $650 per $100k annually / 12
            insurance_monthly = ((property_value / 100000) * Decimal('650')) / 12

        # Step 3: Calculate DTI ratios
        dti_calc = DTICalculator(monthly_gross_income=monthly_gross_income)

        housing_payment = dti_calc.calculate_housing_payment(
            principal_interest=principal_interest,
            property_tax=property_tax_monthly,
            insurance=insurance_monthly,
            hoa_fees=hoa_fees_monthly,
            mortgage_insurance=mortgage_insurance
        )

        other_monthly_debts = (
            car_payments + student_loans + credit_card_payments +
            personal_loans + other_debts
        )

        dti_breakdown = dti_calc.get_dti_breakdown(
            principal_interest=principal_interest,
            property_tax=property_tax_monthly,
            insurance=insurance_monthly,
            hoa_fees=hoa_fees_monthly,
            mortgage_insurance=mortgage_insurance,
            car_payments=car_payments,
            student_loans=student_loans,
            credit_card_payments=credit_card_payments,
            personal_loans=personal_loans,
            other_debts=other_debts
        )

        # Step 4: Check qualification across all loan types
        qualification_results = dti_calc.check_qualification_all_loan_types(
            housing_payment=housing_payment,
            other_monthly_debts=other_monthly_debts,
            credit_score=credit_score,
            loan_amount=loan_amount,
            property_value=property_value,
            compensating_factors=compensating_factors
        )

        # Step 5: Build comprehensive result
        return {
            'qualified': qualification_results['summary']['qualified_for_any'],
            'qualified_loan_types': qualification_results['summary']['qualified_loan_types'],
            'primary_loan_type': loan_type,

            # Income analysis
            'income_analysis': {
                'monthly_gross_income': float(monthly_gross_income),
                'annual_gross_income': float(monthly_gross_income * 12),
                'income_sources': income_data['income_calculation']['income_sources'],
                'income_confidence': income_data['income_calculation']['confidence_score'],
            },

            # Housing payment breakdown
            'housing_payment': {
                'total': float(housing_payment),
                'principal_interest': float(principal_interest),
                'property_tax': float(property_tax_monthly),
                'insurance': float(insurance_monthly),
                'hoa_fees': float(hoa_fees_monthly),
                'mortgage_insurance': float(mortgage_insurance),
            },

            # DTI analysis
            'dti_analysis': {
                'front_end_dti': dti_breakdown['front_end_dti'],
                'back_end_dti': dti_breakdown['back_end_dti'],
                'total_monthly_debts': dti_breakdown['total_debts'],
                'other_debts': float(other_monthly_debts),
                'debt_breakdown': dti_breakdown['debt_components'],
            },

            # Qualification by loan type
            'qualification_by_loan_type': qualification_results['qualification_by_loan_type'],

            # Loan details
            'loan_details': {
                'loan_amount': float(loan_amount),
                'property_value': float(property_value),
                'down_payment': float(down_payment),
                'down_payment_pct': float(down_payment_pct),
                'ltv': float(ltv),
                'interest_rate': float(interest_rate),
                'loan_term_years': loan_term_years,
                'credit_score': credit_score,
            },

            # Document extraction metadata
            'document_extraction': income_data['extraction_metadata'],

            # Timestamp
            'calculated_at': datetime.utcnow().isoformat(),
        }


def run_qualification_example():
    """Example usage of the qualification workflow."""

    workflow = MortgageQualificationWorkflow()

    result = workflow.complete_qualification_workflow(
        # Loan details
        loan_type='fannie_mae',
        loan_amount=Decimal('400000'),
        property_value=Decimal('500000'),
        interest_rate=Decimal('6.5'),
        loan_term_years=30,

        # Borrower
        credit_score=740,

        # Documents (example paths)
        paystub_files=['/path/to/paystub1.pdf', '/path/to/paystub2.pdf'],
        w2_files=['/path/to/w2_2024.pdf', '/path/to/w2_2023.pdf'],

        # Property costs (estimated if not provided)
        property_tax_monthly=Decimal('500'),
        insurance_monthly=Decimal('150'),
        hoa_fees_monthly=Decimal('200'),

        # Other debts
        car_payments=Decimal('450'),
        student_loans=Decimal('250'),
        credit_card_payments=Decimal('100'),

        # Compensating factors
        compensating_factors=['high_credit_score', 'significant_reserves'],
    )

    # Print results
    print("=" * 80)
    print("MORTGAGE QUALIFICATION ANALYSIS")
    print("=" * 80)
    print(f"\nQualified: {result['qualified']}")
    print(f"Qualified for: {', '.join(result['qualified_loan_types'])}")
    print(f"\nMonthly Income: ${result['income_analysis']['monthly_gross_income']:,.2f}")
    print(f"Monthly Housing Payment: ${result['housing_payment']['total']:,.2f}")
    print(f"Total Monthly Debts: ${result['dti_analysis']['total_monthly_debts']:,.2f}")
    print(f"\nFront-End DTI: {result['dti_analysis']['front_end_dti']:.2f}%")
    print(f"Back-End DTI: {result['dti_analysis']['back_end_dti']:.2f}%")
    print("\nQualification by Loan Type:")
    for loan_type, qual in result['qualification_by_loan_type'].items():
        status = "✓" if qual['qualified'] else "✗"
        print(f"  {status} {loan_type}: {qual['your_dti']:.2f}% (max: {qual['max_dti']:.2f}%)")

    return result


if __name__ == '__main__':
    run_qualification_example()
