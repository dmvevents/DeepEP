"""
Income Qualification Engine

Main engine for calculating qualifying income based on loan type and guidelines.
Routes to appropriate guideline (Fannie Mae, FHA, VA, etc.) and applies rules.

Created by: Neumann Rashid AI Development
Date: November 8, 2025
"""

from decimal import Decimal
from typing import Dict, List, Optional
from .guidelines import (
    BaseGuideline,
    FannieMaeGuideline,
    FHAGuideline,
    VAGuideline,
)
from .guidelines.base import IncomeCalculationResult


class IncomeQualificationEngine:
    """
    Main engine for income qualification calculations.

    Routes calculations to appropriate guideline based on loan type.
    Supports:
    - Fannie Mae (Conventional)
    - FHA (Government)
    - VA (Veterans)
    - Freddie Mac (future)
    - USDA (future)
    """

    SUPPORTED_LOAN_TYPES = {
        'fannie_mae': FannieMaeGuideline,
        'conventional': FannieMaeGuideline,  # Alias
        'fha': FHAGuideline,
        'government': FHAGuideline,  # Alias
        'va': VAGuideline,
        'veterans': VAGuideline,  # Alias
    }

    def __init__(
        self,
        loan_type: str,
        loan_amount: Decimal,
        property_value: Decimal
    ):
        """
        Initialize income qualification engine.

        Args:
            loan_type: Type of loan ('fannie_mae', 'fha', 'va', etc.)
            loan_amount: Loan amount
            property_value: Property purchase price or appraised value

        Raises:
            ValueError: If loan type is not supported
        """
        loan_type_normalized = loan_type.lower().replace('-', '_').replace(' ', '_')

        if loan_type_normalized not in self.SUPPORTED_LOAN_TYPES:
            supported = ', '.join(self.SUPPORTED_LOAN_TYPES.keys())
            raise ValueError(
                f"Loan type '{loan_type}' not supported. "
                f"Supported types: {supported}"
            )

        self.loan_type = loan_type_normalized
        self.loan_amount = loan_amount
        self.property_value = property_value

        # Initialize guideline
        guideline_class = self.SUPPORTED_LOAN_TYPES[loan_type_normalized]
        self.guideline: BaseGuideline = guideline_class(loan_amount, property_value)

    def calculate_qualifying_income(
        self,
        w2_documents: Optional[List[Dict]] = None,
        paystub_documents: Optional[List[Dict]] = None,
        tax_return_documents: Optional[List[Dict]] = None,
        bank_statement_documents: Optional[List[Dict]] = None,
        other_income_documents: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Calculate total qualifying income using guideline-specific rules.

        Args:
            w2_documents: List of extracted W-2 data
            paystub_documents: List of extracted pay stub data
            tax_return_documents: List of extracted tax return data
            bank_statement_documents: List of extracted bank statement data
            other_income_documents: List of other income sources

        Returns:
            Dict with income breakdown and qualification details
        """
        # Call guideline-specific calculation
        result: IncomeCalculationResult = self.guideline.calculate_qualifying_income(
            w2_income=w2_documents,
            paystub_income=paystub_documents,
            tax_returns=tax_return_documents,
            bank_statements=bank_statement_documents,
            other_income=other_income_documents,
        )

        # Add guideline info to result
        result_dict = result.to_dict()
        result_dict['loan_type'] = self.loan_type
        result_dict['guideline_name'] = self.guideline.NAME
        result_dict['loan_amount'] = float(self.loan_amount)
        result_dict['property_value'] = float(self.property_value)
        result_dict['ltv'] = float(self.guideline.ltv)

        # Calculate monthly income
        monthly_income = result.total_qualifying_income / 12
        result_dict['monthly_qualifying_income'] = float(monthly_income)

        return result_dict

    def calculate_max_loan_amount(
        self,
        monthly_qualifying_income: Decimal,
        monthly_debts: Decimal,
        monthly_property_tax: Decimal,
        monthly_insurance: Decimal,
        monthly_hoa: Decimal,
        interest_rate: Decimal,
        loan_term_years: int = 30,
        credit_score: int = 700,
        compensating_factors: Optional[List[str]] = None
    ) -> Dict:
        """
        Calculate maximum loan amount borrower qualifies for.

        Works backwards from DTI ratio to determine max loan.

        Args:
            monthly_qualifying_income: Borrower's monthly qualifying income
            monthly_debts: Other monthly debt obligations
            monthly_property_tax: Estimated monthly property tax
            monthly_insurance: Estimated monthly insurance
            monthly_hoa: Monthly HOA/condo fees
            interest_rate: Interest rate as percentage (e.g., 6.5)
            loan_term_years: Loan term in years
            credit_score: Borrower's credit score
            compensating_factors: List of compensating factors

        Returns:
            Dict with max loan amount and breakdown
        """
        if compensating_factors is None:
            compensating_factors = []

        # Get max DTI for this guideline
        max_dti = self.guideline.calculate_max_dti(
            credit_score=credit_score,
            compensating_factors=compensating_factors
        )

        # Calculate max total monthly payment
        max_total_payment = (monthly_qualifying_income * max_dti / 100)

        # Subtract existing debts
        max_housing_payment = max_total_payment - monthly_debts

        # Subtract non-principal/interest housing costs
        max_pi_payment = max_housing_payment - monthly_property_tax - monthly_insurance - monthly_hoa

        # Calculate max loan amount using amortization formula
        # P&I = L * [r(1+r)^n] / [(1+r)^n - 1]
        # Solving for L: L = P&I * [(1+r)^n - 1] / [r(1+r)^n]

        monthly_rate = (interest_rate / 100) / 12
        num_payments = loan_term_years * 12

        if monthly_rate == 0:
            # Handle 0% interest rate edge case
            max_loan = max_pi_payment * num_payments
        else:
            denominator = monthly_rate * ((1 + monthly_rate) ** num_payments)
            numerator = ((1 + monthly_rate) ** num_payments) - 1
            max_loan = max_pi_payment * (numerator / denominator)

        return {
            'max_loan_amount': float(max_loan),
            'max_monthly_payment': float(max_total_payment),
            'max_housing_payment': float(max_housing_payment),
            'max_pi_payment': float(max_pi_payment),
            'max_dti': float(max_dti),
            'monthly_qualifying_income': float(monthly_qualifying_income),
            'monthly_debts': float(monthly_debts),
            'guideline': self.guideline.NAME,
            'interest_rate': float(interest_rate),
            'loan_term_years': loan_term_years,
        }

    def check_qualification(
        self,
        monthly_qualifying_income: Decimal,
        monthly_housing_payment: Decimal,
        monthly_debts: Decimal,
        credit_score: int,
        down_payment_pct: Decimal,
        compensating_factors: Optional[List[str]] = None
    ) -> Dict:
        """
        Check if borrower qualifies for this loan.

        Args:
            monthly_qualifying_income: Monthly qualifying income
            monthly_housing_payment: Total monthly housing payment (PITI)
            monthly_debts: Other monthly debts
            credit_score: Borrower's credit score
            down_payment_pct: Down payment as percentage
            compensating_factors: List of compensating factors

        Returns:
            Dict with qualification decision and details
        """
        if compensating_factors is None:
            compensating_factors = []

        # Calculate DTI ratios
        front_end_dti = (monthly_housing_payment / monthly_qualifying_income * 100)
        back_end_dti = ((monthly_housing_payment + monthly_debts) / monthly_qualifying_income * 100)

        # Get max DTI for this guideline
        max_dti = self.guideline.calculate_max_dti(
            credit_score=credit_score,
            compensating_factors=compensating_factors
        )

        # Check if qualified
        dti_qualified = back_end_dti <= max_dti

        # Additional checks by guideline type
        if self.loan_type in ['fha', 'government']:
            eligibility = self.guideline.check_loan_eligibility(
                credit_score=credit_score,
                down_payment_pct=down_payment_pct,
                dti_ratio=back_end_dti,
                compensating_factors=compensating_factors
            )
        elif self.loan_type in ['va', 'veterans']:
            # VA needs residual income calculation
            # Placeholder - would need actual tax calculations
            residual_income = Decimal('1000')  # TODO: Calculate from actual data
            eligibility = self.guideline.check_loan_eligibility(
                credit_score=credit_score,
                down_payment_pct=down_payment_pct,
                dti_ratio=back_end_dti,
                residual_income=residual_income
            )
        else:
            # Fannie Mae / Conventional
            eligibility = self.guideline.check_loan_eligibility(
                credit_score=credit_score,
                down_payment_pct=down_payment_pct,
                dti_ratio=back_end_dti
            )

        return {
            'qualified': eligibility['eligible'],
            'front_end_dti': float(front_end_dti),
            'back_end_dti': float(back_end_dti),
            'max_dti': float(max_dti),
            'dti_qualified': dti_qualified,
            'reasons': eligibility['reasons'],
            'monthly_qualifying_income': float(monthly_qualifying_income),
            'monthly_housing_payment': float(monthly_housing_payment),
            'monthly_debts': float(monthly_debts),
            'guideline': self.guideline.NAME,
            'loan_type': self.loan_type,
        }

    def get_guideline_summary(self) -> Dict:
        """Get summary of current guideline parameters"""
        summary = self.guideline.get_guideline_summary()
        summary['loan_type'] = self.loan_type
        return summary

    @classmethod
    def get_supported_loan_types(cls) -> List[str]:
        """Get list of supported loan types"""
        return list(cls.SUPPORTED_LOAN_TYPES.keys())
