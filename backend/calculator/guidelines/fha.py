"""
FHA (Federal Housing Administration) Lending Guidelines

Reference: FHA Single Family Housing Policy Handbook (HUD 4000.1)
- Max DTI: 43% (standard), up to 56.99% with compensating factors
- Min Credit Score: 580 (3.5% down), 500 (10% down)
- Min Down Payment: 3.5% (96.5% LTV)
- Income: 2-year average for variable income
- Self-Employment: 2 years tax returns required
- MIP: Required for all FHA loans
"""

from decimal import Decimal
from typing import Dict, List, Optional
from .base import BaseGuideline, IncomeCalculationResult


class FHAGuideline(BaseGuideline):
    """FHA government loan guideline implementation"""

    NAME = "FHA (Government Insured)"
    MAX_DTI_STANDARD = 43
    MAX_DTI_MAXIMUM = 56.99  # With strong compensating factors
    MIN_CREDIT_SCORE_3_5_DOWN = 580  # For 3.5% down payment
    MIN_CREDIT_SCORE_10_DOWN = 500   # For 10% down payment
    MIN_DOWN_PAYMENT_PCT = 3.5

    # FHA specific
    MAX_LTV_STANDARD = 96.5  # 3.5% down
    MAX_LTV_LOW_CREDIT = 90  # 10% down for 500-579 credit score
    UPFRONT_MIP_PCT = 1.75   # Upfront mortgage insurance premium
    ANNUAL_MIP_PCT = 0.85    # Annual MIP for LTV > 95%

    BONUS_CALCULATION_PERIOD_MONTHS = 24
    SELF_EMPLOYMENT_HISTORY_MONTHS = 24

    def calculate_max_dti(
        self,
        credit_score: int,
        compensating_factors: List[str] = None,
        housing_ratio: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate maximum DTI for FHA.

        FHA allows:
        - 43% DTI standard (most common)
        - Up to 56.99% with compensating factors

        Compensating factors for DTI 43-56.99%:
        - Minimal increase in housing payment
        - Significant additional income not considered in DTI
        - Significant additional net worth
        - Borrower has demonstrated ability to save
        - Credit score 620+ with no major derogatory credit
        - Minimal consumer debt
        - Significant residual income
        - Long-term employment in same line of work
        """
        if compensating_factors is None:
            compensating_factors = []

        # Start with standard DTI
        max_dti = Decimal(str(self.MAX_DTI_STANDARD))

        # Count strong compensating factors
        strong_factors = sum([
            'minimal_payment_increase' in compensating_factors,
            'additional_income' in compensating_factors,
            'additional_net_worth' in compensating_factors,
            'savings_ability' in compensating_factors,
            credit_score >= 620,
            'minimal_consumer_debt' in compensating_factors,
            'significant_residual_income' in compensating_factors,
            'long_term_employment' in compensating_factors,
        ])

        # With 2+ strong compensating factors, can extend to higher DTI
        if strong_factors >= 2:
            # FHA can go up to 56.99% with strong compensating factors
            max_dti = Decimal(str(self.MAX_DTI_MAXIMUM))
        elif strong_factors >= 1:
            # With 1 factor, can go to 50%
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
        Calculate qualifying income per FHA guidelines.

        FHA Rules (similar to Fannie Mae):
        - Base salary: Current pay stub or most recent W-2
        - Bonus/OT/Commission: 2-year average, must show continuity
        - Self-employment: 2 years tax returns, add back depreciation
        - Rental income: Schedule E, use net income (more conservative than Fannie)
        - Other income: Case-by-case with 3-year continuity

        Returns:
            IncomeCalculationResult with detailed breakdown
        """
        result = IncomeCalculationResult()
        result.calculation_method = "FHA Government Insured"

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

        # 4. Calculate rental income (FHA: Use net income from Schedule E)
        rental_income_net = Decimal('0')
        for tax_return in tax_returns:
            schedule_e = tax_return.get('schedule_e', {})
            if schedule_e:
                # FHA uses NET rental income (more conservative)
                net_rental = Decimal(str(schedule_e.get('net_rental_income', 0)))
                if net_rental > 0:
                    rental_income_net += net_rental

        if rental_income_net > 0:
            result.rental_income = rental_income_net
            result.notes.append(
                f"Rental income: ${result.rental_income:,.2f} (net income from Schedule E)"
            )

        # 5. Other income (alimony, child support, social security, disability, etc.)
        # FHA is more flexible with other income sources
        for income_item in other_income:
            income_type = income_item.get('type', '')
            amount = Decimal(str(income_item.get('amount', 0)))
            continuity_months = income_item.get('continuity_months', 0)

            # FHA: Require 3-year continuity (or proof of continuation for benefits)
            if continuity_months >= 36 or income_type in ['social_security', 'disability', 'pension']:
                result.other_income += amount
                result.notes.append(f"{income_type}: ${amount:,.2f}")
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
            confidence_factors.append(20)
        if len(w2_income) >= 2:
            confidence_factors.append(15)
        if len(tax_returns) >= 2:
            confidence_factors.append(15)
        if result.total_qualifying_income > 0:
            confidence_factors.append(20)
        if not result.warnings:
            confidence_factors.append(30)

        result.confidence_score = sum(confidence_factors)

        return result

    def calculate_mortgage_insurance(self, loan_amount: Decimal, ltv: Decimal) -> Dict:
        """
        Calculate FHA mortgage insurance premiums.

        FHA requires:
        - Upfront MIP: 1.75% of loan amount (can be financed)
        - Annual MIP: Varies by LTV and loan term

        Returns:
            Dict with upfront and annual MIP amounts
        """
        upfront_mip = loan_amount * (Decimal(str(self.UPFRONT_MIP_PCT)) / 100)

        # Annual MIP varies by LTV
        if ltv <= 95:
            annual_mip_pct = Decimal('0.80')
        else:
            annual_mip_pct = Decimal(str(self.ANNUAL_MIP_PCT))

        annual_mip = loan_amount * (annual_mip_pct / 100)
        monthly_mip = annual_mip / 12

        return {
            'upfront_mip': float(upfront_mip),
            'annual_mip': float(annual_mip),
            'monthly_mip': float(monthly_mip),
            'upfront_mip_pct': float(self.UPFRONT_MIP_PCT),
            'annual_mip_pct': float(annual_mip_pct),
        }

    def check_loan_eligibility(
        self,
        credit_score: int,
        down_payment_pct: Decimal,
        dti_ratio: Decimal,
        compensating_factors: List[str] = None
    ) -> Dict:
        """
        Check if borrower meets FHA eligibility requirements.

        Args:
            credit_score: Borrower's credit score
            down_payment_pct: Down payment as percentage
            dti_ratio: Back-end DTI ratio
            compensating_factors: List of compensating factors

        Returns:
            Dict with 'eligible' bool and 'reasons' list
        """
        if compensating_factors is None:
            compensating_factors = []

        eligible = True
        reasons = []

        # Credit score and down payment combination
        ltv = 100 - down_payment_pct

        if credit_score < self.MIN_CREDIT_SCORE_10_DOWN:
            eligible = False
            reasons.append(
                f"Credit score {credit_score} below FHA minimum {self.MIN_CREDIT_SCORE_10_DOWN}"
            )
        elif credit_score < self.MIN_CREDIT_SCORE_3_5_DOWN:
            # 500-579: Requires 10% down payment
            if down_payment_pct < 10:
                eligible = False
                reasons.append(
                    f"Credit score {credit_score} requires minimum 10% down payment"
                )
            if ltv > self.MAX_LTV_LOW_CREDIT:
                eligible = False
                reasons.append(
                    f"LTV {ltv:.1f}% exceeds maximum {self.MAX_LTV_LOW_CREDIT}% "
                    f"for credit score {credit_score}"
                )
        else:
            # 580+: 3.5% down payment allowed
            if ltv > self.MAX_LTV_STANDARD:
                eligible = False
                reasons.append(
                    f"LTV {ltv:.1f}% exceeds maximum {self.MAX_LTV_STANDARD}%"
                )

        # DTI ratio
        max_dti = self.calculate_max_dti(credit_score, compensating_factors)
        if dti_ratio > max_dti:
            eligible = False
            reasons.append(
                f"DTI {dti_ratio:.1f}% exceeds maximum {max_dti:.1f}% "
                f"(with {len(compensating_factors)} compensating factors)"
            )

        if eligible:
            reasons.append("Borrower meets all FHA eligibility requirements")

        return {
            'eligible': eligible,
            'reasons': reasons,
            'guideline': self.NAME,
            'max_dti': float(max_dti),
            'max_ltv': float(self.MAX_LTV_STANDARD if credit_score >= 580 else self.MAX_LTV_LOW_CREDIT),
            'mip_required': True,
        }
