"""
Base Guideline Class

Abstract base class for all lending guidelines.
Each specific guideline (Fannie Mae, FHA, etc.) inherits from this.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime


class IncomeCalculationResult:
    """Container for income calculation results"""

    def __init__(self):
        self.base_income: Decimal = Decimal('0')
        self.bonus_income: Decimal = Decimal('0')
        self.overtime_income: Decimal = Decimal('0')
        self.commission_income: Decimal = Decimal('0')
        self.self_employment_income: Decimal = Decimal('0')
        self.rental_income: Decimal = Decimal('0')
        self.other_income: Decimal = Decimal('0')
        self.total_qualifying_income: Decimal = Decimal('0')
        self.calculation_method: str = ""
        self.confidence_score: int = 100
        self.notes: List[str] = []
        self.warnings: List[str] = []

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'base_income': float(self.base_income),
            'bonus_income': float(self.bonus_income),
            'overtime_income': float(self.overtime_income),
            'commission_income': float(self.commission_income),
            'self_employment_income': float(self.self_employment_income),
            'rental_income': float(self.rental_income),
            'other_income': float(self.other_income),
            'total_qualifying_income': float(self.total_qualifying_income),
            'calculation_method': self.calculation_method,
            'confidence_score': self.confidence_score,
            'notes': self.notes,
            'warnings': self.warnings,
        }


class BaseGuideline(ABC):
    """
    Abstract base class for all lending guidelines.

    Each guideline must implement:
    - DTI limits
    - Income calculation rules
    - Qualification logic
    """

    # Default values (override in subclasses)
    NAME = "Base Guideline"
    MAX_DTI_AUTO = 50
    MAX_DTI_MANUAL = 45
    MIN_CREDIT_SCORE = 620
    MIN_DOWN_PAYMENT_PCT = 3

    # Income calculation periods
    BONUS_CALCULATION_PERIOD_MONTHS = 24  # 2-year average
    SELF_EMPLOYMENT_HISTORY_MONTHS = 24
    CONTINUITY_REQUIREMENT_MONTHS = 24

    def __init__(self, loan_amount: Decimal, property_value: Decimal):
        self.loan_amount = loan_amount
        self.property_value = property_value
        self.ltv = (loan_amount / property_value * 100) if property_value > 0 else 0

    @abstractmethod
    def calculate_max_dti(self, credit_score: int, compensating_factors: List[str] = None) -> Decimal:
        """
        Calculate maximum DTI ratio for this guideline.

        Args:
            credit_score: Borrower's credit score
            compensating_factors: List of compensating factors (reserves, low LTV, etc.)

        Returns:
            Maximum back-end DTI ratio as decimal (e.g., 50.0 for 50%)
        """
        pass

    @abstractmethod
    def calculate_qualifying_income(
        self,
        w2_income: Optional[List[Dict]] = None,
        paystub_income: Optional[List[Dict]] = None,
        tax_returns: Optional[List[Dict]] = None,
        bank_statements: Optional[List[Dict]] = None,
        other_income: Optional[List[Dict]] = None,
    ) -> IncomeCalculationResult:
        """
        Calculate total qualifying income based on guideline-specific rules.

        Args:
            w2_income: List of W-2 data (last 2 years)
            paystub_income: List of pay stub data (recent)
            tax_returns: List of tax return data (last 2 years for self-employed)
            bank_statements: Bank statements (for deposits, rental income)
            other_income: Other income sources

        Returns:
            IncomeCalculationResult with detailed breakdown
        """
        pass

    def calculate_base_salary(self, w2_income: List[Dict], paystubs: List[Dict]) -> Decimal:
        """
        Calculate base salary from W-2s and pay stubs.

        Standard approach:
        - Use most recent pay stub for current income
        - Verify continuity with W-2s
        - Check for increasing/decreasing trend
        """
        if not w2_income and not paystubs:
            return Decimal('0')

        # Get most recent pay stub
        if paystubs:
            most_recent_paystub = max(paystubs, key=lambda x: x.get('pay_period_end', ''))
            annual_income = most_recent_paystub.get('gross_income_ytd', 0)

            # Annualize if we're not at year-end
            if annual_income > 0:
                return Decimal(str(annual_income))

        # Fall back to most recent W-2
        if w2_income:
            most_recent_w2 = max(w2_income, key=lambda x: x.get('tax_year', 0))
            return Decimal(str(most_recent_w2.get('box_1_wages', 0)))

        return Decimal('0')

    def calculate_bonus_overtime_commission(
        self,
        w2_income: List[Dict],
        paystubs: List[Dict],
        calculation_period_months: int = 24
    ) -> Dict[str, Decimal]:
        """
        Calculate variable income (bonus, overtime, commission).

        Standard approach:
        - 2-year average (24 months)
        - Must show 2-year history of receipt
        - Declining trend may not be usable

        Returns:
            Dict with 'bonus', 'overtime', 'commission' keys
        """
        result = {
            'bonus': Decimal('0'),
            'overtime': Decimal('0'),
            'commission': Decimal('0'),
        }

        if len(w2_income) < 2:
            return result

        # Get last 2 years
        sorted_w2s = sorted(w2_income, key=lambda x: x.get('tax_year', 0), reverse=True)[:2]

        # Calculate average for each category
        for category in ['bonus', 'overtime', 'commission']:
            values = [Decimal(str(w2.get(category, 0))) for w2 in sorted_w2s if w2.get(category)]
            if len(values) == 2:
                # Check for declining trend
                if values[0] < values[1] * Decimal('0.8'):  # More than 20% decline
                    # Use lower amount or don't count
                    result[category] = values[0]
                else:
                    # Average the two years
                    result[category] = sum(values) / 2

        return result

    def calculate_self_employment_income(self, tax_returns: List[Dict]) -> Decimal:
        """
        Calculate self-employment income from tax returns.

        Standard approach:
        - Require 2 years of tax returns
        - Use Schedule C net profit (or Schedule K-1)
        - Add back non-cash deductions (depreciation)
        - 2-year average
        - Declining trend = use lower year
        """
        if len(tax_returns) < 2:
            return Decimal('0')

        # Get last 2 years
        sorted_returns = sorted(tax_returns, key=lambda x: x.get('tax_year', 0), reverse=True)[:2]

        net_profits = []
        for tax_return in sorted_returns:
            net_profit = Decimal(str(tax_return.get('schedule_c_net_profit', 0)))
            depreciation = Decimal(str(tax_return.get('depreciation', 0)))

            # Add back depreciation (non-cash expense)
            adjusted_profit = net_profit + depreciation
            net_profits.append(adjusted_profit)

        if len(net_profits) != 2:
            return Decimal('0')

        # Check for declining trend
        if net_profits[0] < net_profits[1] * Decimal('0.8'):  # More than 20% decline
            return net_profits[0]  # Use lower year

        # Average the two years
        return sum(net_profits) / 2

    def check_income_continuity(self, income_history: List[Dict]) -> bool:
        """
        Check if income shows required continuity.

        Most guidelines require:
        - 2 years of history in same line of work
        - No unexplained gaps > 30 days
        - Consistent or increasing income
        """
        if len(income_history) < 2:
            return False

        # Check for gaps
        sorted_history = sorted(income_history, key=lambda x: x.get('date', ''))

        for i in range(1, len(sorted_history)):
            prev_date = datetime.fromisoformat(sorted_history[i-1].get('date', ''))
            curr_date = datetime.fromisoformat(sorted_history[i].get('date', ''))

            gap_days = (curr_date - prev_date).days
            if gap_days > 30:
                return False

        return True

    def get_guideline_summary(self) -> Dict:
        """Return summary of guideline parameters"""
        return {
            'name': self.NAME,
            'max_dti_auto': float(self.MAX_DTI_AUTO),
            'max_dti_manual': float(self.MAX_DTI_MANUAL),
            'min_credit_score': self.MIN_CREDIT_SCORE,
            'min_down_payment_pct': float(self.MIN_DOWN_PAYMENT_PCT),
            'bonus_calculation_period_months': self.BONUS_CALCULATION_PERIOD_MONTHS,
            'self_employment_history_months': self.SELF_EMPLOYMENT_HISTORY_MONTHS,
        }
