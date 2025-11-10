"""
VA (Veterans Affairs) Lending Guidelines

Reference: VA Lender's Handbook and VA Pamphlet 26-7
- Max DTI: 41% (guideline), flexible with residual income test
- Min Credit Score: No official minimum (typically 620)
- Min Down Payment: 0% (100% LTV)
- Income: 2-year average for variable income
- Self-Employment: 2 years tax returns required
- Funding Fee: 2.3% first use (0% down), waived for disabled veterans
- Residual Income: Key qualifier unique to VA
"""

from decimal import Decimal
from typing import Dict, List, Optional
from .base import BaseGuideline, IncomeCalculationResult


class VAGuideline(BaseGuideline):
    """VA veterans loan guideline implementation"""

    NAME = "VA (Veterans Affairs)"
    MAX_DTI_GUIDELINE = 41  # Guideline, but flexible with residual income
    MAX_DTI_ABSOLUTE = 60   # Absolute maximum with strong residual income
    MIN_CREDIT_SCORE = 620  # Not official VA requirement, but lender typical
    MIN_DOWN_PAYMENT_PCT = 0  # VA allows 100% financing

    # VA specific
    MAX_LTV = 100  # No down payment required
    FUNDING_FEE_FIRST_USE = 2.3  # 2.3% for first use, 0% down
    FUNDING_FEE_SUBSEQUENT = 3.6  # 3.6% for subsequent use
    FUNDING_FEE_RESERVE = 2.3  # Reserves/National Guard

    BONUS_CALCULATION_PERIOD_MONTHS = 24
    SELF_EMPLOYMENT_HISTORY_MONTHS = 24

    # Residual Income Tables (Monthly) - VA Pamphlet 26-7, Revised
    # These are minimum required residual income by region, family size, loan amount
    RESIDUAL_INCOME_TABLES = {
        'northeast': {  # CT, ME, MA, NH, NJ, NY, PA, RI, VT
            'loan_under_80k': {1: 450, 2: 755, 3: 909, 4: 1025, 5: 1062},
            'loan_80k_plus': {1: 550, 2: 888, 3: 1042, 4: 1158, 5: 1195},
        },
        'midwest': {  # IL, IN, IA, KS, MI, MN, MO, NE, ND, OH, SD, WI
            'loan_under_80k': {1: 382, 2: 641, 3: 772, 4: 868, 5: 902},
            'loan_80k_plus': {1: 465, 2: 755, 3: 886, 4: 982, 5: 1016},
        },
        'south': {  # AL, AR, DE, DC, FL, GA, KY, LA, MD, MS, NC, OK, SC, TN, TX, VA, WV
            'loan_under_80k': {1: 382, 2: 641, 3: 772, 4: 868, 5: 902},
            'loan_80k_plus': {1: 465, 2: 755, 3: 886, 4: 982, 5: 1016},
        },
        'west': {  # AK, AZ, CA, CO, HI, ID, MT, NV, NM, OR, UT, WA, WY
            'loan_under_80k': {1: 425, 2: 713, 3: 859, 4: 967, 5: 1004},
            'loan_80k_plus': {1: 518, 2: 840, 3: 986, 4: 1094, 5: 1131},
        },
    }

    def calculate_max_dti(
        self,
        credit_score: int,
        compensating_factors: List[str] = None,
        residual_income: Optional[Decimal] = None,
        family_size: int = 2,
        region: str = 'south'
    ) -> Decimal:
        """
        Calculate maximum DTI for VA.

        VA is unique:
        - 41% DTI is a guideline, not a hard limit
        - Residual income test is more important
        - Can exceed 41% DTI if residual income is strong

        Residual Income = Gross Income - (Taxes + Housing + Debts)
        Must meet minimum by region, family size, and loan amount

        Args:
            credit_score: Borrower's credit score
            compensating_factors: List of compensating factors
            residual_income: Calculated residual income
            family_size: Number in household
            region: 'northeast', 'midwest', 'south', or 'west'
        """
        if compensating_factors is None:
            compensating_factors = []

        # Start with guideline DTI
        max_dti = Decimal(str(self.MAX_DTI_GUIDELINE))

        # VA is flexible if residual income is strong
        if residual_income:
            # Get minimum required residual income
            loan_category = 'loan_80k_plus' if self.loan_amount >= 80000 else 'loan_under_80k'
            family_size_capped = min(family_size, 5)  # Table caps at 5

            min_residual = self.RESIDUAL_INCOME_TABLES.get(region, {}).get(
                loan_category, {}
            ).get(family_size_capped, 0)

            # If residual income exceeds minimum by 20%+, can extend DTI
            if residual_income >= Decimal(str(min_residual)) * Decimal('1.2'):
                max_dti = Decimal('50')  # Can go higher with strong residual

            # If residual income is exceptional (50%+ above minimum), DTI almost unlimited
            if residual_income >= Decimal(str(min_residual)) * Decimal('1.5'):
                max_dti = Decimal(str(self.MAX_DTI_ABSOLUTE))

        return max_dti

    def calculate_residual_income(
        self,
        gross_monthly_income: Decimal,
        federal_tax: Decimal,
        state_tax: Decimal,
        fica_medicare: Decimal,
        housing_payment: Decimal,
        other_debts: Decimal
    ) -> Decimal:
        """
        Calculate residual income for VA qualification.

        Residual Income = Gross Income - (All Taxes + Housing + All Debts)

        This is what's left over for food, clothing, transportation, etc.

        Args:
            gross_monthly_income: Total monthly gross income
            federal_tax: Monthly federal income tax
            state_tax: Monthly state income tax
            fica_medicare: Monthly FICA + Medicare
            housing_payment: Total housing payment (PITI)
            other_debts: All other monthly debt obligations

        Returns:
            Residual income amount
        """
        residual = (
            gross_monthly_income -
            federal_tax -
            state_tax -
            fica_medicare -
            housing_payment -
            other_debts
        )

        return max(residual, Decimal('0'))

    def calculate_qualifying_income(
        self,
        w2_income: Optional[List[Dict]] = None,
        paystub_income: Optional[List[Dict]] = None,
        tax_returns: Optional[List[Dict]] = None,
        bank_statements: Optional[List[Dict]] = None,
        other_income: Optional[List[Dict]] = None,
    ) -> IncomeCalculationResult:
        """
        Calculate qualifying income per VA guidelines.

        VA Rules (similar to Fannie Mae/FHA):
        - Base salary: Current pay stub or most recent W-2
        - Bonus/OT/Commission: 2-year average, must show continuity
        - Self-employment: 2 years tax returns, add back depreciation
        - Rental income: 75% of gross or net from Schedule E
        - Military income: BAH (Basic Allowance for Housing) counts
        - Disability income: VA disability compensation counts (not taxed)

        Returns:
            IncomeCalculationResult with detailed breakdown
        """
        result = IncomeCalculationResult()
        result.calculation_method = "VA Veterans Affairs"

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

        # 4. Calculate rental income (VA: Use 75% of gross or net from Schedule E)
        rental_income_gross = Decimal('0')
        for tax_return in tax_returns:
            schedule_e = tax_return.get('schedule_e', {})
            if schedule_e:
                gross_rents = Decimal(str(schedule_e.get('gross_rents', 0)))
                rental_income_gross += gross_rents

        if rental_income_gross > 0:
            result.rental_income = rental_income_gross * Decimal('0.75')
            result.notes.append(
                f"Rental income: ${result.rental_income:,.2f} "
                f"(75% of ${rental_income_gross:,.2f} gross rents)"
            )

        # 5. Other income - VA is flexible with military and disability income
        for income_item in other_income:
            income_type = income_item.get('type', '')
            amount = Decimal(str(income_item.get('amount', 0)))
            continuity_months = income_item.get('continuity_months', 0)

            # VA disability and military allowances count fully
            if income_type in ['va_disability', 'bah', 'bas', 'military_allowance']:
                result.other_income += amount
                result.notes.append(f"{income_type}: ${amount:,.2f} (military/VA income)")
            elif continuity_months >= 36:
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

    def calculate_funding_fee(
        self,
        loan_amount: Decimal,
        down_payment_pct: Decimal,
        first_use: bool = True,
        disabled_veteran: bool = False,
        reserve_guard: bool = False
    ) -> Dict:
        """
        Calculate VA funding fee.

        Funding fee varies by:
        - First use vs. subsequent use
        - Down payment amount
        - Regular military vs. reserves/guard
        - Disabled veterans are exempt

        Returns:
            Dict with funding fee amount and percentage
        """
        if disabled_veteran:
            return {
                'funding_fee': 0.0,
                'funding_fee_pct': 0.0,
                'reason': 'Waived for disabled veteran',
            }

        # Determine funding fee percentage
        if down_payment_pct >= 10:
            fee_pct = 1.4 if first_use else 1.4
        elif down_payment_pct >= 5:
            fee_pct = 1.65 if first_use else 1.65
        else:
            # 0% down
            if first_use:
                fee_pct = self.FUNDING_FEE_FIRST_USE
            else:
                fee_pct = self.FUNDING_FEE_SUBSEQUENT

        # Reserves/Guard pay slightly higher
        if reserve_guard:
            fee_pct += 0.25

        funding_fee = loan_amount * (Decimal(str(fee_pct)) / 100)

        return {
            'funding_fee': float(funding_fee),
            'funding_fee_pct': float(fee_pct),
            'can_be_financed': True,
            'first_use': first_use,
        }

    def check_loan_eligibility(
        self,
        credit_score: int,
        down_payment_pct: Decimal,
        dti_ratio: Decimal,
        residual_income: Decimal,
        family_size: int = 2,
        region: str = 'south'
    ) -> Dict:
        """
        Check if borrower meets VA eligibility requirements.

        Args:
            credit_score: Borrower's credit score
            down_payment_pct: Down payment as percentage
            dti_ratio: Back-end DTI ratio
            residual_income: Calculated residual income
            family_size: Household size
            region: Geographic region for residual income table

        Returns:
            Dict with 'eligible' bool and 'reasons' list
        """
        eligible = True
        reasons = []

        # Credit score (lender overlay, not VA requirement)
        if credit_score < self.MIN_CREDIT_SCORE:
            eligible = False
            reasons.append(
                f"Credit score {credit_score} below typical lender minimum {self.MIN_CREDIT_SCORE}"
            )

        # DTI ratio (guideline, but flexible with residual income)
        max_dti = self.calculate_max_dti(
            credit_score,
            residual_income=residual_income,
            family_size=family_size,
            region=region
        )

        if dti_ratio > max_dti:
            # Check residual income
            loan_category = 'loan_80k_plus' if self.loan_amount >= 80000 else 'loan_under_80k'
            family_size_capped = min(family_size, 5)
            min_residual = self.RESIDUAL_INCOME_TABLES.get(region, {}).get(
                loan_category, {}
            ).get(family_size_capped, 0)

            if residual_income < Decimal(str(min_residual)):
                eligible = False
                reasons.append(
                    f"DTI {dti_ratio:.1f}% exceeds guideline {self.MAX_DTI_GUIDELINE}% "
                    f"and residual income ${residual_income:,.2f} below minimum ${min_residual:,.2f}"
                )
            else:
                reasons.append(
                    f"DTI {dti_ratio:.1f}% exceeds guideline but residual income "
                    f"${residual_income:,.2f} meets requirement"
                )

        # Check residual income requirement
        loan_category = 'loan_80k_plus' if self.loan_amount >= 80000 else 'loan_under_80k'
        family_size_capped = min(family_size, 5)
        min_residual = self.RESIDUAL_INCOME_TABLES.get(region, {}).get(
            loan_category, {}
        ).get(family_size_capped, 0)

        if residual_income < Decimal(str(min_residual)):
            eligible = False
            reasons.append(
                f"Residual income ${residual_income:,.2f} below minimum ${min_residual:,.2f} "
                f"for {region} region, family size {family_size}"
            )

        if eligible:
            reasons.append("Borrower meets all VA eligibility requirements")

        return {
            'eligible': eligible,
            'reasons': reasons,
            'guideline': self.NAME,
            'max_dti': float(max_dti),
            'max_ltv': 100.0,
            'residual_income_required': min_residual,
            'residual_income_actual': float(residual_income),
            'funding_fee_required': True,
        }
