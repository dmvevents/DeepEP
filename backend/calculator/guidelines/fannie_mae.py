"""
Fannie Mae (Conventional) Lending Guidelines

Reference: Fannie Mae Selling Guide
- Max DTI: 50% (automated underwriting), 45% (manual underwriting)
- Min Credit Score: 620
- Min Down Payment: 3% (97% LTV max)
- Income: 2-year average for variable income
- Self-Employment: 2 years tax returns required
"""

from decimal import Decimal
from typing import Dict, List, Optional
from .base import BaseGuideline, IncomeCalculationResult


class FannieMaeGuideline(BaseGuideline):
    """Fannie Mae conventional loan guideline implementation"""

    NAME = "Fannie Mae (Conventional)"
    MAX_DTI_AUTO = 50  # Desktop Underwriter (DU) automated
    MAX_DTI_MANUAL = 45  # Manual underwriting
    MIN_CREDIT_SCORE = 620
    MIN_DOWN_PAYMENT_PCT = 3

    # Fannie Mae specific
    MAX_LTV = 97  # 3% down
    MAX_LTV_INVESTMENT = 75  # Investment property
    RESERVES_REQUIRED_MONTHS = 2  # For manual underwriting

    BONUS_CALCULATION_PERIOD_MONTHS = 24
    SELF_EMPLOYMENT_HISTORY_MONTHS = 24

    def calculate_max_dti(
        self,
        credit_score: int,
        compensating_factors: List[str] = None,
        automated_underwriting: bool = True
    ) -> Decimal:
        """
        Calculate maximum DTI for Fannie Mae.

        Fannie Mae allows:
        - 50% DTI with automated underwriting (Desktop Underwriter)
        - 45% DTI with manual underwriting
        - Up to 50% with strong compensating factors

        Compensating factors:
        - High credit score (740+)
        - Low LTV (60% or less)
        - Significant reserves (12+ months)
        - Minimal payment increase
        """
        if compensating_factors is None:
            compensating_factors = []

        # Start with base DTI
        if automated_underwriting:
            max_dti = Decimal(str(self.MAX_DTI_AUTO))
        else:
            max_dti = Decimal(str(self.MAX_DTI_MANUAL))

        # Adjust for compensating factors (manual underwriting)
        if not automated_underwriting:
            strong_factors = sum([
                credit_score >= 740,
                self.ltv <= 60,
                'significant_reserves' in compensating_factors,
                'minimal_payment_increase' in compensating_factors,
            ])

            # With 2+ strong compensating factors, can go to 50%
            if strong_factors >= 2:
                max_dti = Decimal('50')

        return max_dti

    def calculate_qualifying_income(
        self,
        w2_income: Optional[List[Dict]] = None,
        paystub_income: Optional[List[Dict]] = None,
        tax_returns: Optional[List[Dict]] = None,
        bank_statements: Optional[List[Dict]] = None,
        other_income: Optional[List[Dict]] = None,
    ) -> IncomeCalculationResult:
        """
        Calculate qualifying income per Fannie Mae guidelines.

        Fannie Mae Rules:
        - Base salary: Current pay stub or most recent W-2
        - Bonus/OT/Commission: 2-year average, must show continuity
        - Self-employment: 2 years tax returns, add back depreciation
        - Rental income: Schedule E, 75% of gross rents
        - Other income: Case-by-case with 3-year continuity

        Returns:
            IncomeCalculationResult with detailed breakdown
        """
        result = IncomeCalculationResult()
        result.calculation_method = "Fannie Mae Conventional"

        # Initialize defaults
        w2_income = w2_income or []
        paystub_income = paystub_income or []
        tax_returns = tax_returns or []
        bank_statements = bank_statements or []
        other_income = other_income or []

        # 1. Calculate base salary
        if w2_income or paystub_income:
            result.base_income = self.calculate_base_salary(w2_income, paystub_income)
            result.notes.append(f"Base income: ${result.base_income:,.2f} from W-2/paystub")

        # 2. Calculate variable income (bonus, overtime, commission)
        if len(w2_income) >= 2:
            variable_income = self.calculate_bonus_overtime_commission(
                w2_income,
                paystub_income,
                self.BONUS_CALCULATION_PERIOD_MONTHS
            )

            result.bonus_income = variable_income['bonus']
            result.overtime_income = variable_income['overtime']
            result.commission_income = variable_income['commission']

            if result.bonus_income > 0:
                result.notes.append(f"Bonus income: ${result.bonus_income:,.2f} (2-year average)")
            if result.overtime_income > 0:
                result.notes.append(f"Overtime income: ${result.overtime_income:,.2f} (2-year average)")
            if result.commission_income > 0:
                result.notes.append(f"Commission income: ${result.commission_income:,.2f} (2-year average)")
        elif w2_income:
            result.warnings.append("Less than 2 years of variable income history - not counted")

        # 3. Calculate self-employment income
        if len(tax_returns) >= 2:
            result.self_employment_income = self.calculate_self_employment_income(tax_returns)
            if result.self_employment_income > 0:
                result.notes.append(
                    f"Self-employment income: ${result.self_employment_income:,.2f} "
                    "(2-year average, depreciation added back)"
                )
        elif tax_returns:
            result.warnings.append("Less than 2 years of self-employment history - not counted")

        # 4. Calculate rental income (Fannie Mae: 75% of gross rents)
        rental_income_gross = Decimal('0')
        for tax_return in tax_returns:
            schedule_e = tax_return.get('schedule_e', {})
            if schedule_e:
                gross_rents = Decimal(str(schedule_e.get('gross_rents', 0)))
                rental_income_gross += gross_rents

        if rental_income_gross > 0:
            # Fannie Mae: Use 75% of gross rents
            result.rental_income = rental_income_gross * Decimal('0.75')
            result.notes.append(
                f"Rental income: ${result.rental_income:,.2f} "
                f"(75% of ${rental_income_gross:,.2f} gross rents)"
            )

        # 5. Other income (alimony, child support, social security, etc.)
        for income_item in other_income:
            income_type = income_item.get('type', '')
            amount = Decimal(str(income_item.get('amount', 0)))
            continuity_months = income_item.get('continuity_months', 0)

            # Fannie Mae: Require 3-year continuity for most other income
            if continuity_months >= 36:
                result.other_income += amount
                result.notes.append(f"{income_type}: ${amount:,.2f} (36+ months continuity)")
            else:
                result.warnings.append(
                    f"{income_type} not counted - requires 36 months continuity, "
                    f"only {continuity_months} months shown"
                )

        # 6. Calculate total qualifying income
        result.total_qualifying_income = (
            result.base_income +
            result.bonus_income +
            result.overtime_income +
            result.commission_income +
            result.self_employment_income +
            result.rental_income +
            result.other_income
        )

        # 7. Confidence scoring
        confidence_factors = []

        if w2_income or paystub_income:
            confidence_factors.append(20)  # Base income present
        if len(w2_income) >= 2:
            confidence_factors.append(15)  # 2-year W-2 history
        if len(tax_returns) >= 2:
            confidence_factors.append(15)  # 2-year tax return history
        if result.total_qualifying_income > 0:
            confidence_factors.append(20)  # Income calculated
        if not result.warnings:
            confidence_factors.append(30)  # No warnings

        result.confidence_score = sum(confidence_factors)

        return result

    def check_loan_eligibility(
        self,
        credit_score: int,
        down_payment_pct: Decimal,
        dti_ratio: Decimal,
        property_type: str = "primary"
    ) -> Dict:
        """
        Check if borrower meets Fannie Mae eligibility requirements.

        Args:
            credit_score: Borrower's credit score
            down_payment_pct: Down payment as percentage
            dti_ratio: Back-end DTI ratio
            property_type: 'primary', 'secondary', 'investment'

        Returns:
            Dict with 'eligible' bool and 'reasons' list
        """
        eligible = True
        reasons = []

        # Credit score
        if credit_score < self.MIN_CREDIT_SCORE:
            eligible = False
            reasons.append(
                f"Credit score {credit_score} below minimum {self.MIN_CREDIT_SCORE}"
            )

        # LTV/Down payment
        ltv = 100 - down_payment_pct
        max_ltv = self.MAX_LTV if property_type == "primary" else self.MAX_LTV_INVESTMENT

        if ltv > max_ltv:
            eligible = False
            reasons.append(
                f"LTV {ltv:.1f}% exceeds maximum {max_ltv}% for {property_type} property"
            )

        # DTI ratio
        max_dti = self.calculate_max_dti(credit_score, automated_underwriting=True)
        if dti_ratio > max_dti:
            eligible = False
            reasons.append(
                f"DTI {dti_ratio:.1f}% exceeds maximum {max_dti:.1f}%"
            )

        if eligible:
            reasons.append("Borrower meets all Fannie Mae eligibility requirements")

        return {
            'eligible': eligible,
            'reasons': reasons,
            'guideline': self.NAME,
            'max_dti': float(max_dti),
            'max_ltv': float(max_ltv),
        }
