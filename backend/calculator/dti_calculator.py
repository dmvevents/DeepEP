"""
DTI (Debt-to-Income) Calculator

Calculates front-end and back-end DTI ratios for mortgage qualification.

Front-End DTI = Housing Payment / Gross Income
Back-End DTI = (Housing Payment + All Debts) / Gross Income

Created by: Neumann Rashid AI Development
Date: November 8, 2025
"""

from decimal import Decimal
from typing import Dict, List, Optional
from .guidelines import (
    FannieMaeGuideline,
    FHAGuideline,
    VAGuideline,
)


class DTICalculator:
    """
    Calculate Debt-to-Income ratios for mortgage qualification.

    Two ratios calculated:
    1. Front-End DTI (Housing Ratio): Housing payment / Gross income
    2. Back-End DTI (Total Debt Ratio): (Housing + All Debts) / Gross income

    Most lenders focus on back-end DTI, but some have front-end limits too.
    """

    def __init__(self, monthly_gross_income: Decimal):
        """
        Initialize DTI calculator.

        Args:
            monthly_gross_income: Borrower's monthly gross income
        """
        if monthly_gross_income <= 0:
            raise ValueError("Monthly gross income must be greater than zero")

        self.monthly_gross_income = monthly_gross_income

    def calculate_housing_payment(
        self,
        principal_interest: Decimal,
        property_tax: Decimal,
        insurance: Decimal,
        hoa_fees: Decimal = Decimal('0'),
        mortgage_insurance: Decimal = Decimal('0')
    ) -> Decimal:
        """
        Calculate total monthly housing payment (PITI + HOA + MI).

        Args:
            principal_interest: Monthly P&I payment
            property_tax: Monthly property tax
            insurance: Monthly homeowners insurance
            hoa_fees: Monthly HOA/condo fees
            mortgage_insurance: Monthly mortgage insurance (PMI/MIP)

        Returns:
            Total monthly housing payment
        """
        return (
            principal_interest +
            property_tax +
            insurance +
            hoa_fees +
            mortgage_insurance
        )

    def calculate_total_debts(
        self,
        housing_payment: Decimal,
        car_payments: Decimal = Decimal('0'),
        student_loans: Decimal = Decimal('0'),
        credit_card_payments: Decimal = Decimal('0'),
        personal_loans: Decimal = Decimal('0'),
        other_debts: Decimal = Decimal('0')
    ) -> Decimal:
        """
        Calculate total monthly debt obligations.

        Args:
            housing_payment: Total housing payment (PITI)
            car_payments: Monthly car/auto loan payments
            student_loans: Monthly student loan payments
            credit_card_payments: Minimum monthly credit card payments
            personal_loans: Monthly personal loan payments
            other_debts: Other monthly debt obligations

        Returns:
            Total monthly debts
        """
        return (
            housing_payment +
            car_payments +
            student_loans +
            credit_card_payments +
            personal_loans +
            other_debts
        )

    def calculate_dti_ratios(
        self,
        housing_payment: Decimal,
        other_monthly_debts: Decimal
    ) -> Dict:
        """
        Calculate both front-end and back-end DTI ratios.

        Args:
            housing_payment: Total monthly housing payment (PITI + HOA + MI)
            other_monthly_debts: All other monthly debt obligations

        Returns:
            Dict with both DTI ratios and qualification info
        """
        # Front-end DTI (housing ratio)
        front_end_dti = (housing_payment / self.monthly_gross_income) * 100

        # Back-end DTI (total debt ratio)
        total_debts = housing_payment + other_monthly_debts
        back_end_dti = (total_debts / self.monthly_gross_income) * 100

        return {
            'front_end_dti': float(front_end_dti),
            'back_end_dti': float(back_end_dti),
            'housing_payment': float(housing_payment),
            'other_monthly_debts': float(other_monthly_debts),
            'total_monthly_debts': float(total_debts),
            'monthly_gross_income': float(self.monthly_gross_income),
        }

    def check_qualification_all_loan_types(
        self,
        housing_payment: Decimal,
        other_monthly_debts: Decimal,
        credit_score: int,
        loan_amount: Decimal,
        property_value: Decimal,
        compensating_factors: Optional[List[str]] = None
    ) -> Dict:
        """
        Check qualification against all major loan types.

        Args:
            housing_payment: Total monthly housing payment
            other_monthly_debts: Other monthly debts
            credit_score: Borrower's credit score
            loan_amount: Loan amount
            property_value: Property value
            compensating_factors: List of compensating factors

        Returns:
            Dict with qualification status for each loan type
        """
        if compensating_factors is None:
            compensating_factors = []

        # Calculate DTI ratios
        dti_ratios = self.calculate_dti_ratios(housing_payment, other_monthly_debts)
        back_end_dti = Decimal(str(dti_ratios['back_end_dti']))
        down_payment_pct = ((property_value - loan_amount) / property_value * 100)

        results = {
            'dti_ratios': dti_ratios,
            'qualification_by_loan_type': {},
        }

        # Check Fannie Mae (Conventional)
        fannie = FannieMaeGuideline(loan_amount, property_value)
        fannie_max_dti = fannie.calculate_max_dti(
            credit_score=credit_score,
            compensating_factors=compensating_factors,
            automated_underwriting=True
        )
        results['qualification_by_loan_type']['fannie_mae'] = {
            'qualified': back_end_dti <= fannie_max_dti,
            'max_dti': float(fannie_max_dti),
            'your_dti': float(back_end_dti),
            'margin': float(fannie_max_dti - back_end_dti),
        }

        # Check FHA
        fha = FHAGuideline(loan_amount, property_value)
        fha_max_dti = fha.calculate_max_dti(
            credit_score=credit_score,
            compensating_factors=compensating_factors
        )
        results['qualification_by_loan_type']['fha'] = {
            'qualified': back_end_dti <= fha_max_dti,
            'max_dti': float(fha_max_dti),
            'your_dti': float(back_end_dti),
            'margin': float(fha_max_dti - back_end_dti),
        }

        # Check VA (requires residual income - placeholder for now)
        va = VAGuideline(loan_amount, property_value)
        va_max_dti = va.calculate_max_dti(
            credit_score=credit_score,
            compensating_factors=compensating_factors
        )
        results['qualification_by_loan_type']['va'] = {
            'qualified': back_end_dti <= va_max_dti,
            'max_dti': float(va_max_dti),
            'your_dti': float(back_end_dti),
            'margin': float(va_max_dti - back_end_dti),
            'note': 'VA also requires residual income test',
        }

        # Summary
        qualified_for = [
            loan_type for loan_type, result in results['qualification_by_loan_type'].items()
            if result['qualified']
        ]

        results['summary'] = {
            'qualified_for_any': len(qualified_for) > 0,
            'qualified_loan_types': qualified_for,
            'best_loan_type': qualified_for[0] if qualified_for else None,
        }

        return results

    def calculate_max_affordable_payment(
        self,
        target_dti: Decimal,
        other_monthly_debts: Decimal
    ) -> Decimal:
        """
        Calculate maximum affordable housing payment for target DTI.

        Args:
            target_dti: Target DTI ratio (e.g., 43 for 43%)
            other_monthly_debts: Other monthly debts

        Returns:
            Maximum affordable housing payment
        """
        # Max total debts = Income * (Target DTI / 100)
        max_total_debts = self.monthly_gross_income * (target_dti / 100)

        # Max housing payment = Max total debts - Other debts
        max_housing_payment = max_total_debts - other_monthly_debts

        return max(max_housing_payment, Decimal('0'))

    def get_dti_breakdown(
        self,
        principal_interest: Decimal,
        property_tax: Decimal,
        insurance: Decimal,
        hoa_fees: Decimal,
        mortgage_insurance: Decimal,
        car_payments: Decimal,
        student_loans: Decimal,
        credit_card_payments: Decimal,
        personal_loans: Decimal,
        other_debts: Decimal
    ) -> Dict:
        """
        Get detailed DTI breakdown showing each component.

        Args:
            All individual debt components

        Returns:
            Detailed breakdown with percentages
        """
        # Calculate housing payment
        housing_payment = self.calculate_housing_payment(
            principal_interest=principal_interest,
            property_tax=property_tax,
            insurance=insurance,
            hoa_fees=hoa_fees,
            mortgage_insurance=mortgage_insurance
        )

        # Calculate each component as percentage of income
        components = {
            'principal_interest': float(principal_interest),
            'property_tax': float(property_tax),
            'insurance': float(insurance),
            'hoa_fees': float(hoa_fees),
            'mortgage_insurance': float(mortgage_insurance),
            'car_payments': float(car_payments),
            'student_loans': float(student_loans),
            'credit_card_payments': float(credit_card_payments),
            'personal_loans': float(personal_loans),
            'other_debts': float(other_debts),
        }

        # Calculate percentage for each
        component_percentages = {}
        for name, amount in components.items():
            pct = (Decimal(str(amount)) / self.monthly_gross_income) * 100
            component_percentages[name] = float(pct)

        # Calculate DTI ratios
        other_debts_total = (
            car_payments + student_loans + credit_card_payments +
            personal_loans + other_debts
        )

        dti_ratios = self.calculate_dti_ratios(housing_payment, other_debts_total)

        return {
            'monthly_gross_income': float(self.monthly_gross_income),
            'housing_payment': float(housing_payment),
            'other_debts': float(other_debts_total),
            'total_debts': float(housing_payment + other_debts_total),
            'front_end_dti': dti_ratios['front_end_dti'],
            'back_end_dti': dti_ratios['back_end_dti'],
            'debt_components': components,
            'component_percentages': component_percentages,
        }

    @staticmethod
    def get_dti_guidelines_summary() -> Dict:
        """
        Get summary of DTI guidelines for all loan types.

        Returns:
            Dict with DTI limits for each loan type
        """
        return {
            'fannie_mae': {
                'name': 'Fannie Mae (Conventional)',
                'max_dti_auto': 50,
                'max_dti_manual': 45,
                'notes': 'Desktop Underwriter allows up to 50%',
            },
            'freddie_mac': {
                'name': 'Freddie Mac (Conventional)',
                'max_dti_auto': 43,
                'max_dti_manual': 45,
                'notes': 'Loan Product Advisor allows up to 43%',
            },
            'fha': {
                'name': 'FHA (Government)',
                'max_dti_standard': 43,
                'max_dti_maximum': 56.99,
                'notes': 'Up to 56.99% with compensating factors',
            },
            'usda': {
                'name': 'USDA (Rural Housing)',
                'max_dti': 41,
                'notes': 'Income limits also apply',
            },
            'va': {
                'name': 'VA (Veterans)',
                'max_dti_guideline': 41,
                'notes': 'Flexible with residual income test',
            },
        }