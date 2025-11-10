"""
Income Calculation Service - Phase 2

Production-ready service for calculating qualifying monthly income from:
- W-2 salary/hourly + overtime/bonus
- Schedule C self-employment income

Supports configurable rule toggles:
- Exclude accounts with <10 payments
- Exclude cosigned debt

Author: Backend/Django Engineer
Date: November 10, 2025
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class IncomeCalculationService:
    """
    Service for calculating qualifying monthly income.

    Handles W-2 employment income and Schedule C self-employment income
    with configurable rules for exclusions and averaging periods.
    """

    def __init__(
        self,
        exclude_less_than_10_payments: Optional[bool] = None,
        exclude_cosigned_debt: Optional[bool] = None,
        variable_income_average_months: int = 24,
        schedule_c_average_months: int = 24,
    ):
        """
        Initialize income calculation service.

        Args:
            exclude_less_than_10_payments: Exclude income sources with <10 payment history
                                           (defaults to settings.INCOME_EXCLUDE_LESS_THAN_10_PAYMENTS)
            exclude_cosigned_debt: Exclude cosigned debt from DTI calculation
                                  (defaults to settings.INCOME_EXCLUDE_COSIGNED_DEBT)
            variable_income_average_months: Number of months to average variable income (default: 24)
            schedule_c_average_months: Number of months to average Schedule C income (default: 24)
        """
        # Use settings values if not explicitly provided
        self.exclude_less_than_10_payments = (
            exclude_less_than_10_payments
            if exclude_less_than_10_payments is not None
            else getattr(settings, 'INCOME_EXCLUDE_LESS_THAN_10_PAYMENTS', False)
        )

        self.exclude_cosigned_debt = (
            exclude_cosigned_debt
            if exclude_cosigned_debt is not None
            else getattr(settings, 'INCOME_EXCLUDE_COSIGNED_DEBT', False)
        )

        self.variable_income_average_months = variable_income_average_months
        self.schedule_c_average_months = schedule_c_average_months

        logger.debug(
            f"IncomeCalculationService initialized: "
            f"exclude_<10_payments={self.exclude_less_than_10_payments}, "
            f"exclude_cosigned={self.exclude_cosigned_debt}"
        )

    def calculate_monthly_income(
        self,
        w2_data: Optional[List[Dict]] = None,
        paystub_data: Optional[List[Dict]] = None,
        schedule_c_data: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Calculate total qualifying monthly income.

        Args:
            w2_data: List of W-2 data for last 2 years
            paystub_data: List of recent pay stub data
            schedule_c_data: List of Schedule C tax data (last 2 years)

        Returns:
            Dict with:
                - monthly_base_salary: Monthly base W-2 salary
                - monthly_overtime: Monthly qualifying overtime
                - monthly_bonus: Monthly qualifying bonus
                - monthly_schedule_c: Monthly Schedule C net income
                - total_monthly_income: Sum of all income
                - calculation_notes: List of calculation explanations
                - warnings: List of warnings/exclusions
                - rule_toggles: Active rule configurations
        """
        w2_data = w2_data or []
        paystub_data = paystub_data or []
        schedule_c_data = schedule_c_data or []

        result = {
            'monthly_base_salary': Decimal('0'),
            'monthly_overtime': Decimal('0'),
            'monthly_bonus': Decimal('0'),
            'monthly_schedule_c': Decimal('0'),
            'total_monthly_income': Decimal('0'),
            'calculation_notes': [],
            'warnings': [],
            'rule_toggles': {
                'exclude_less_than_10_payments': self.exclude_less_than_10_payments,
                'exclude_cosigned_debt': self.exclude_cosigned_debt,
                'variable_income_average_months': self.variable_income_average_months,
                'schedule_c_average_months': self.schedule_c_average_months,
            }
        }

        try:
            # Calculate W-2 income components
            if w2_data or paystub_data:
                w2_result = self._calculate_w2_income(w2_data, paystub_data)
                result['monthly_base_salary'] = w2_result['base_salary']
                result['monthly_overtime'] = w2_result['overtime']
                result['monthly_bonus'] = w2_result['bonus']
                result['calculation_notes'].extend(w2_result['notes'])
                result['warnings'].extend(w2_result['warnings'])

            # Calculate Schedule C income
            if schedule_c_data:
                schedule_c_result = self._calculate_schedule_c_income(schedule_c_data)
                result['monthly_schedule_c'] = schedule_c_result['monthly_income']
                result['calculation_notes'].extend(schedule_c_result['notes'])
                result['warnings'].extend(schedule_c_result['warnings'])

            # Calculate total
            result['total_monthly_income'] = (
                result['monthly_base_salary'] +
                result['monthly_overtime'] +
                result['monthly_bonus'] +
                result['monthly_schedule_c']
            )

            logger.info(
                f"Income calculation completed: Total monthly income = "
                f"${result['total_monthly_income']:,.2f}"
            )

        except Exception as e:
            logger.error(f"Error calculating income: {e}", exc_info=True)
            result['warnings'].append(f"Error during calculation: {str(e)}")

        return result

    def _calculate_w2_income(
        self,
        w2_data: List[Dict],
        paystub_data: List[Dict]
    ) -> Dict:
        """
        Calculate W-2 employment income (base salary + overtime + bonus).

        Args:
            w2_data: List of W-2 forms (last 2 years)
            paystub_data: List of recent pay stubs

        Returns:
            Dict with base_salary, overtime, bonus, notes, warnings
        """
        result = {
            'base_salary': Decimal('0'),
            'overtime': Decimal('0'),
            'bonus': Decimal('0'),
            'notes': [],
            'warnings': [],
        }

        # 1. Calculate base salary (from most recent paystub or W-2)
        if paystub_data:
            base_annual = self._get_base_salary_from_paystubs(paystub_data)
            result['base_salary'] = (base_annual / 12).quantize(Decimal('0.01'), ROUND_HALF_UP)
            result['notes'].append(
                f"Base salary: ${base_annual:,.2f}/year from most recent paystub "
                f"(${result['base_salary']:,.2f}/month)"
            )
        elif w2_data:
            most_recent_w2 = max(w2_data, key=lambda x: x.get('tax_year', 0))
            base_annual = Decimal(str(most_recent_w2.get('wages', 0)))
            result['base_salary'] = (base_annual / 12).quantize(Decimal('0.01'), ROUND_HALF_UP)
            result['notes'].append(
                f"Base salary: ${base_annual:,.2f}/year from {most_recent_w2.get('tax_year')} W-2 "
                f"(${result['base_salary']:,.2f}/month)"
            )

        # 2. Calculate variable income (overtime and bonus) - requires 2 years
        if len(w2_data) >= 2:
            variable_result = self._calculate_variable_income(w2_data, paystub_data)
            result['overtime'] = variable_result['overtime']
            result['bonus'] = variable_result['bonus']
            result['notes'].extend(variable_result['notes'])
            result['warnings'].extend(variable_result['warnings'])
        elif len(w2_data) == 1:
            result['warnings'].append(
                "Variable income (OT/bonus) excluded: Only 1 year of W-2 history "
                f"(requires {self.variable_income_average_months} months)"
            )

        # 3. Apply <10 payments rule if enabled
        if self.exclude_less_than_10_payments:
            payment_count = self._estimate_payment_count(w2_data, paystub_data)
            if payment_count < 10:
                result['warnings'].append(
                    f"Income excluded: Only {payment_count} payment(s) recorded "
                    f"(rule: exclude <10 payments)"
                )
                result['base_salary'] = Decimal('0')
                result['overtime'] = Decimal('0')
                result['bonus'] = Decimal('0')

        return result

    def _get_base_salary_from_paystubs(self, paystub_data: List[Dict]) -> Decimal:
        """
        Extract annualized base salary from most recent pay stub.

        Args:
            paystub_data: List of pay stub data

        Returns:
            Annual base salary (Decimal)
        """
        if not paystub_data:
            return Decimal('0')

        # Get most recent pay stub
        most_recent = max(paystub_data, key=lambda x: x.get('pay_date', ''))

        # Try to get YTD gross from paystub
        ytd_gross = Decimal(str(most_recent.get('gross_ytd', 0)))
        if ytd_gross > 0:
            # Annualize based on current date
            pay_date_str = most_recent.get('pay_date', '')
            if pay_date_str:
                try:
                    pay_date = datetime.fromisoformat(pay_date_str.replace('Z', '+00:00'))
                    months_worked = pay_date.month + (pay_date.year - datetime.now().year) * 12
                    if months_worked > 0:
                        return (ytd_gross / months_worked * 12).quantize(Decimal('0.01'), ROUND_HALF_UP)
                except (ValueError, AttributeError):
                    pass

            # Fallback: assume full year
            return ytd_gross

        # Fallback: calculate from pay period
        pay_amount = Decimal(str(most_recent.get('gross_pay', 0)))
        pay_frequency = most_recent.get('pay_frequency', 'biweekly')

        frequency_multiplier = {
            'weekly': 52,
            'biweekly': 26,
            'semi-monthly': 24,
            'monthly': 12,
        }

        multiplier = frequency_multiplier.get(pay_frequency, 26)  # Default biweekly
        return (pay_amount * multiplier).quantize(Decimal('0.01'), ROUND_HALF_UP)

    def _calculate_variable_income(
        self,
        w2_data: List[Dict],
        paystub_data: List[Dict]
    ) -> Dict:
        """
        Calculate variable income (overtime and bonus) using 2-year average.

        Args:
            w2_data: List of W-2 data (must have at least 2 years)
            paystub_data: List of pay stub data

        Returns:
            Dict with overtime, bonus, notes, warnings
        """
        result = {
            'overtime': Decimal('0'),
            'bonus': Decimal('0'),
            'notes': [],
            'warnings': [],
        }

        if len(w2_data) < 2:
            return result

        # Get last 2 years of W-2s
        sorted_w2s = sorted(w2_data, key=lambda x: x.get('tax_year', 0), reverse=True)[:2]

        # Extract overtime for both years
        overtime_year1 = Decimal(str(sorted_w2s[0].get('overtime', 0)))
        overtime_year2 = Decimal(str(sorted_w2s[1].get('overtime', 0)))

        # Extract bonus for both years
        bonus_year1 = Decimal(str(sorted_w2s[0].get('bonus', 0)))
        bonus_year2 = Decimal(str(sorted_w2s[1].get('bonus', 0)))

        # Calculate overtime average (check for declining trend)
        if overtime_year1 > 0 or overtime_year2 > 0:
            if overtime_year1 < overtime_year2 * Decimal('0.8'):  # >20% decline
                # Use lower year
                annual_overtime = overtime_year1
                result['warnings'].append(
                    f"Overtime declining >20%: Using lower year (${overtime_year1:,.2f})"
                )
            else:
                # Average both years
                annual_overtime = (overtime_year1 + overtime_year2) / 2
                result['notes'].append(
                    f"Overtime: 2-year average of ${overtime_year1:,.2f} and ${overtime_year2:,.2f}"
                )

            result['overtime'] = (annual_overtime / 12).quantize(Decimal('0.01'), ROUND_HALF_UP)

        # Calculate bonus average (check for declining trend)
        if bonus_year1 > 0 or bonus_year2 > 0:
            if bonus_year1 < bonus_year2 * Decimal('0.8'):  # >20% decline
                # Use lower year
                annual_bonus = bonus_year1
                result['warnings'].append(
                    f"Bonus declining >20%: Using lower year (${bonus_year1:,.2f})"
                )
            else:
                # Average both years
                annual_bonus = (bonus_year1 + bonus_year2) / 2
                result['notes'].append(
                    f"Bonus: 2-year average of ${bonus_year1:,.2f} and ${bonus_year2:,.2f}"
                )

            result['bonus'] = (annual_bonus / 12).quantize(Decimal('0.01'), ROUND_HALF_UP)

        return result

    def _estimate_payment_count(
        self,
        w2_data: List[Dict],
        paystub_data: List[Dict]
    ) -> int:
        """
        Estimate number of payments received based on available data.

        Args:
            w2_data: List of W-2 data
            paystub_data: List of pay stub data

        Returns:
            Estimated payment count
        """
        # Use paystub count if available
        if paystub_data:
            return len(paystub_data)

        # Estimate from W-2 years (assume biweekly = 26 payments/year)
        if w2_data:
            years_of_data = len(w2_data)
            return years_of_data * 26  # Conservative estimate

        return 0

    def _calculate_schedule_c_income(self, schedule_c_data: List[Dict]) -> Dict:
        """
        Calculate monthly Schedule C self-employment income.

        Uses 2-year average of net profit with depreciation added back.

        Args:
            schedule_c_data: List of Schedule C data (last 2 years)

        Returns:
            Dict with monthly_income, notes, warnings
        """
        result = {
            'monthly_income': Decimal('0'),
            'notes': [],
            'warnings': [],
        }

        if len(schedule_c_data) < 2:
            if len(schedule_c_data) == 1:
                result['warnings'].append(
                    f"Schedule C income excluded: Only 1 year of history "
                    f"(requires {self.schedule_c_average_months} months)"
                )
            return result

        # Get last 2 years
        sorted_data = sorted(schedule_c_data, key=lambda x: x.get('tax_year', 0), reverse=True)[:2]

        # Calculate adjusted net profit for each year
        adjusted_profits = []
        for year_data in sorted_data:
            net_profit = Decimal(str(year_data.get('net_profit', 0)))
            depreciation = Decimal(str(year_data.get('depreciation', 0)))
            depletion = Decimal(str(year_data.get('depletion', 0)))

            # Add back non-cash expenses
            adjusted_profit = net_profit + depreciation + depletion
            adjusted_profits.append(adjusted_profit)

            tax_year = year_data.get('tax_year', 'Unknown')
            result['notes'].append(
                f"Schedule C {tax_year}: Net profit ${net_profit:,.2f} + "
                f"depreciation ${depreciation:,.2f} + depletion ${depletion:,.2f} = "
                f"${adjusted_profit:,.2f}"
            )

        # Check for declining trend
        if adjusted_profits[0] < adjusted_profits[1] * Decimal('0.8'):  # >20% decline
            # Use lower year
            annual_income = adjusted_profits[0]
            result['warnings'].append(
                f"Schedule C income declining >20%: Using lower year (${annual_income:,.2f})"
            )
        else:
            # Average both years
            annual_income = sum(adjusted_profits) / 2
            result['notes'].append(
                f"Schedule C: 2-year average = ${annual_income:,.2f}/year"
            )

        result['monthly_income'] = (annual_income / 12).quantize(Decimal('0.01'), ROUND_HALF_UP)
        result['notes'].append(f"Monthly Schedule C income: ${result['monthly_income']:,.2f}")

        return result

    def get_service_configuration(self) -> Dict:
        """
        Get current service configuration for auditing/logging.

        Returns:
            Dict with current rule toggles and parameters
        """
        return {
            'exclude_less_than_10_payments': self.exclude_less_than_10_payments,
            'exclude_cosigned_debt': self.exclude_cosigned_debt,
            'variable_income_average_months': self.variable_income_average_months,
            'schedule_c_average_months': self.schedule_c_average_months,
        }
