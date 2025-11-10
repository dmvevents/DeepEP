"""
Mortgage Calculation Engine

Implements CFPB Loan Estimate calculations with all sections.
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MortgageCalculator:
    """
    Main mortgage calculator class implementing CFPB Loan Estimate calculations
    """

    def __init__(self, tax_data: Dict[str, Any]):
        """
        Initialize calculator with tax data

        Args:
            tax_data: Dictionary containing all tax rates and fees for the jurisdiction
        """
        self.tax_data = tax_data

    def calculate(
        self,
        property_value: Decimal,
        loan_amount: Decimal,
        down_payment: Decimal,
        interest_rate: Decimal,
        loan_term_years: int,
        closing_date: datetime,
        loan_type: str = 'conventional',
        property_type: str = 'single_family',
        first_time_homebuyer: bool = False,
        zip_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate complete loan estimate

        Returns:
            Dictionary with all CFPB Loan Estimate sections
        """
        # Validate inputs
        self._validate_inputs(property_value, loan_amount, down_payment, interest_rate)

        # Calculate each section
        results = {
            'section_a': self._calculate_section_a(
                loan_amount, interest_rate, loan_term_years
            ),
            'section_b': self._calculate_section_b(
                loan_amount, interest_rate, loan_term_years,
                property_value, loan_type, closing_date
            ),
            'section_c': self._calculate_section_c(
                property_value, loan_amount, down_payment,
                first_time_homebuyer
            ),
            'section_e': self._calculate_section_e(
                property_value, first_time_homebuyer
            ),
            'section_g': self._calculate_section_g(
                property_value, loan_amount, closing_date, zip_code
            ),
            'section_h': self._calculate_section_h(
                property_value, loan_amount
            ),
        }

        # Calculate totals
        results['summary'] = self._calculate_summary(results)

        return results

    def _validate_inputs(
        self,
        property_value: Decimal,
        loan_amount: Decimal,
        down_payment: Decimal,
        interest_rate: Decimal
    ):
        """Validate calculation inputs"""
        if property_value <= 0:
            raise ValueError("Property value must be positive")

        if loan_amount <= 0:
            raise ValueError("Loan amount must be positive")

        if loan_amount > property_value:
            raise ValueError("Loan amount cannot exceed property value")

        if down_payment < 0:
            raise ValueError("Down payment cannot be negative")

        if abs((property_value - down_payment) - loan_amount) > Decimal('1'):
            raise ValueError("Loan amount must equal property value minus down payment")

        if interest_rate < 0 or interest_rate > 20:
            raise ValueError("Interest rate must be between 0% and 20%")

    def _calculate_section_a(
        self,
        loan_amount: Decimal,
        interest_rate: Decimal,
        loan_term_years: int
    ) -> Dict[str, Any]:
        """
        Section A: Loan Terms

        Returns:
            - Loan amount
            - Interest rate
            - Monthly principal & interest
            - Prepayment penalty info
        """
        monthly_pi = self._calculate_monthly_payment(
            loan_amount, interest_rate, loan_term_years
        )

        return {
            'loan_amount': float(loan_amount),
            'interest_rate': float(interest_rate),
            'loan_term_years': loan_term_years,
            'loan_term_months': loan_term_years * 12,
            'monthly_principal_and_interest': float(monthly_pi),
            'prepayment_penalty': False,  # Typically no penalty for conventional
            'balloon_payment': False,
        }

    def _calculate_section_b(
        self,
        loan_amount: Decimal,
        interest_rate: Decimal,
        loan_term_years: int,
        property_value: Decimal,
        loan_type: str,
        closing_date: datetime
    ) -> Dict[str, Any]:
        """
        Section B: Projected Payments

        Returns:
            - Principal & interest
            - Mortgage insurance
            - Estimated escrow
            - Estimated total monthly payment
        """
        monthly_pi = self._calculate_monthly_payment(
            loan_amount, interest_rate, loan_term_years
        )

        # Calculate LTV ratio
        ltv = (loan_amount / property_value) * 100

        # Mortgage insurance (if LTV > 80%)
        mortgage_insurance = self._calculate_mortgage_insurance(
            loan_amount, property_value, loan_type
        )

        # Estimated escrow (property tax + homeowners insurance)
        monthly_escrow = self._calculate_monthly_escrow(property_value, closing_date)

        # Total monthly payment
        total_monthly = monthly_pi + mortgage_insurance + monthly_escrow

        return {
            'monthly_principal_and_interest': float(monthly_pi),
            'mortgage_insurance': float(mortgage_insurance),
            'estimated_escrow': float(monthly_escrow),
            'estimated_total_monthly_payment': float(total_monthly),
            'ltv_ratio': float(ltv),
            'escrow_breakdown': {
                'property_tax': float(monthly_escrow * Decimal('0.6')),  # Approximate split
                'homeowners_insurance': float(monthly_escrow * Decimal('0.4')),
            }
        }

    def _calculate_section_c(
        self,
        property_value: Decimal,
        loan_amount: Decimal,
        down_payment: Decimal,
        first_time_homebuyer: bool
    ) -> Dict[str, Any]:
        """
        Section C: Costs at Closing

        Returns:
            - Closing costs subtotal
            - Cash to close
        """
        # Get all closing costs
        section_e = self._calculate_section_e(property_value, first_time_homebuyer)
        section_g = self._calculate_section_g_simple(property_value, loan_amount)
        section_h = self._calculate_section_h(property_value, loan_amount)

        # Sum all costs
        total_closing_costs = (
            Decimal(str(section_e['total_taxes_and_fees'])) +
            Decimal(str(section_g['total_initial_escrow'])) +
            Decimal(str(section_h['total_other_costs']))
        )

        # Cash to close = down payment + closing costs
        cash_to_close = down_payment + total_closing_costs

        return {
            'closing_costs_subtotal': float(total_closing_costs),
            'down_payment': float(down_payment),
            'cash_to_close': float(cash_to_close),
            'breakdown': {
                'section_e_total': float(section_e['total_taxes_and_fees']),
                'section_g_total': float(section_g['total_initial_escrow']),
                'section_h_total': float(section_h['total_other_costs']),
            }
        }

    def _calculate_section_e(
        self,
        property_value: Decimal,
        first_time_homebuyer: bool
    ) -> Dict[str, Any]:
        """
        Section E: Taxes and Other Government Fees

        Uses scraped tax data to calculate:
        - Recording fees
        - Transfer taxes
        - Recordation taxes
        """
        recording_fees = self._calculate_recording_fees()
        transfer_taxes = self._calculate_transfer_taxes(
            property_value, first_time_homebuyer
        )
        recordation_taxes = self._calculate_recordation_taxes(property_value)

        total = recording_fees + transfer_taxes + recordation_taxes

        return {
            'recording_fees': float(recording_fees),
            'transfer_taxes': float(transfer_taxes),
            'recordation_taxes': float(recordation_taxes),
            'total_taxes_and_fees': float(total),
            'sources': self.tax_data.get('sources', [])
        }

    def _calculate_section_g(
        self,
        property_value: Decimal,
        loan_amount: Decimal,
        closing_date: datetime,
        zip_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Section G: Initial Escrow Payment at Closing

        Calculates:
        - Homeowners insurance prepaid and escrow
        - Mortgage insurance (if applicable)
        - Property tax prepaid and escrow
        """
        # Get annual amounts
        annual_hoi = self._get_annual_homeowners_insurance(property_value)
        annual_property_tax = self._get_annual_property_tax(property_value, zip_code)

        # Calculate property tax proration
        tax_proration = self._calculate_property_tax_proration(
            annual_property_tax, closing_date
        )

        # Initial escrow deposit (typically 2-3 months)
        hoi_escrow_months = 2
        property_tax_escrow_months = 3

        hoi_monthly = annual_hoi / 12
        property_tax_monthly = annual_property_tax / 12

        hoi_escrow = hoi_monthly * hoi_escrow_months
        property_tax_escrow = property_tax_monthly * property_tax_escrow_months

        # Prepaid amounts
        hoi_prepaid = hoi_monthly  # Usually 1 month prepaid
        property_tax_prepaid = Decimal(str(tax_proration['seller_owes_buyer']))

        total_escrow = hoi_escrow + property_tax_escrow + hoi_prepaid + property_tax_prepaid

        return {
            'homeowners_insurance': {
                'prepaid': float(hoi_prepaid),
                'initial_escrow_deposit': float(hoi_escrow),
                'monthly_amount': float(hoi_monthly),
                'total_months_escrow': hoi_escrow_months,
            },
            'property_tax': {
                'prepaid': float(property_tax_prepaid),
                'initial_escrow_deposit': float(property_tax_escrow),
                'monthly_amount': float(property_tax_monthly),
                'total_months_escrow': property_tax_escrow_months,
                'proration_details': tax_proration,
            },
            'total_initial_escrow': float(total_escrow),
            'annual_property_tax': float(annual_property_tax),
            'annual_hoi': float(annual_hoi),
        }

    def _calculate_section_g_simple(
        self,
        property_value: Decimal,
        loan_amount: Decimal
    ) -> Dict[str, Any]:
        """Simplified Section G for Section C calculations"""
        annual_hoi = self._get_annual_homeowners_insurance(property_value)
        annual_property_tax = self._get_annual_property_tax(property_value)

        monthly_hoi = annual_hoi / 12
        monthly_tax = annual_property_tax / 12

        # Approximate initial escrow (2-3 months each)
        total_escrow = (monthly_hoi * 2) + (monthly_tax * 3) + monthly_hoi

        return {
            'total_initial_escrow': float(total_escrow)
        }

    def _calculate_section_h(
        self,
        property_value: Decimal,
        loan_amount: Decimal
    ) -> Dict[str, Any]:
        """
        Section H: Other Costs

        Includes:
        - Title services
        - Title insurance
        - Lender's title insurance
        - Owner's title insurance (optional)
        """
        # Title fees (approximate based on property value)
        title_search = Decimal('250')
        title_exam = Decimal('200')

        # Title insurance (typically 0.5% of loan amount)
        lenders_title_insurance = loan_amount * Decimal('0.005')

        # Owner's title insurance (optional, typically 0.5% of property value)
        owners_title_insurance = property_value * Decimal('0.005')

        total = title_search + title_exam + lenders_title_insurance + owners_title_insurance

        return {
            'title_search_fee': float(title_search),
            'title_examination_fee': float(title_exam),
            'lenders_title_insurance': float(lenders_title_insurance),
            'owners_title_insurance': float(owners_title_insurance),
            'total_other_costs': float(total),
        }

    def _calculate_monthly_payment(
        self,
        principal: Decimal,
        annual_rate: Decimal,
        years: int
    ) -> Decimal:
        """
        Calculate monthly mortgage payment using amortization formula

        Formula: M = P * [r(1+r)^n] / [(1+r)^n - 1]
        Where:
            M = Monthly payment
            P = Principal loan amount
            r = Monthly interest rate (annual rate / 12 / 100)
            n = Number of payments (years * 12)
        """
        if annual_rate == 0:
            return principal / Decimal(years * 12)

        monthly_rate = annual_rate / Decimal('12') / Decimal('100')
        num_payments = years * 12

        # Calculate (1 + r)^n
        factor = (Decimal('1') + monthly_rate) ** num_payments

        # Calculate monthly payment
        monthly_payment = principal * (monthly_rate * factor) / (factor - Decimal('1'))

        return monthly_payment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _calculate_mortgage_insurance(
        self,
        loan_amount: Decimal,
        property_value: Decimal,
        loan_type: str
    ) -> Decimal:
        """
        Calculate monthly mortgage insurance (PMI/MIP)

        PMI typically required when LTV > 80%
        FHA requires MIP regardless of LTV
        Rate depends on LTV and loan type
        """
        ltv = (loan_amount / property_value) * 100

        # FHA loans require MIP regardless of LTV
        if loan_type == 'fha':
            # FHA MIP is 0.85% of loan amount annually for most loans
            annual_mip = loan_amount * Decimal('0.0085')
            return (annual_mip / 12).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Conventional loans only require PMI when LTV > 80%
        if ltv <= 80:
            return Decimal('0')

        # Conventional PMI rates by LTV
        if ltv > 95:
            pmi_rate = Decimal('0.015')  # 1.5%
        elif ltv > 90:
            pmi_rate = Decimal('0.01')   # 1.0%
        elif ltv > 85:
            pmi_rate = Decimal('0.007')  # 0.7%
        else:
            pmi_rate = Decimal('0.005')  # 0.5%

        annual_pmi = loan_amount * pmi_rate
        return (annual_pmi / 12).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _calculate_monthly_escrow(
        self,
        property_value: Decimal,
        closing_date: datetime
    ) -> Decimal:
        """Calculate monthly escrow amount (property tax + insurance)"""
        annual_tax = self._get_annual_property_tax(property_value)
        annual_insurance = self._get_annual_homeowners_insurance(property_value)

        monthly_escrow = (annual_tax + annual_insurance) / 12

        return monthly_escrow.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _get_annual_property_tax(
        self,
        property_value: Decimal,
        zip_code: Optional[str] = None
    ) -> Decimal:
        """
        Calculate annual property tax from scraped tax data

        Applies:
        - Assessment ratio
        - Base tax rate (composite_rate_per_100)
        - Municipality overlay (if zip code provided)
        - Special assessments
        """
        tax_info = self.tax_data.get('property_tax', {})

        # Get assessment ratio (what percentage of market value is taxed)
        assessment_ratio = Decimal(str(tax_info.get('assessment_ratio', 100))) / 100

        # Calculate assessed value
        assessed_value = property_value * assessment_ratio

        # Get composite rate per $100 (enhanced schema)
        # Try new schema first, fallback to old schema
        composite_rate_per_100 = tax_info.get('composite_rate_per_100')
        if composite_rate_per_100 is not None:
            # Enhanced schema: rate per $100
            rate = Decimal(str(composite_rate_per_100)) / 100
        else:
            # Legacy schema: total_rate
            total_rate = Decimal(str(tax_info.get('total_rate', 0.01)))
            # Check if rate is in mills (per $1000) or percentage
            if total_rate > 1:
                # Likely in mills, convert to percentage
                rate = total_rate / 1000
            else:
                rate = total_rate

        # Apply municipality overlay if zip code provided
        if zip_code:
            municipalities = tax_info.get('municipalities', [])
            for muni in municipalities:
                if zip_code in muni.get('zip_codes', []):
                    # Enhanced schema: composite_rate_per_100
                    muni_composite = muni.get('composite_rate_per_100')
                    if muni_composite is not None:
                        # Use municipality's composite rate (replaces base rate)
                        rate = Decimal(str(muni_composite)) / 100
                    else:
                        # Legacy: add municipality_rate_per_100 or millage
                        muni_rate = muni.get('municipality_rate_per_100') or muni.get('millage', 0)
                        muni_rate = Decimal(str(muni_rate))
                        if muni_rate > 1:
                            muni_rate = muni_rate / 1000
                        else:
                            muni_rate = muni_rate / 100
                        rate += muni_rate
                    break

        # Calculate base annual tax
        annual_tax = assessed_value * rate

        # Add special assessments (flat annual amounts)
        special_assessments = tax_info.get('special_assessments', [])
        for assessment in special_assessments:
            annual_amount = Decimal(str(assessment.get('annual_amount', 0)))
            annual_tax += annual_amount

        return annual_tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _get_annual_homeowners_insurance(
        self,
        property_value: Decimal,
        risk_factors: Optional[Dict[str, bool]] = None
    ) -> Decimal:
        """
        Estimate annual homeowners insurance from scraped data

        Enhanced schema supports:
        - Base premium per $100k OR avg_rate_per_1000
        - Risk modifiers (flood_zone, coastal, wildfire, etc.)
        - Dwelling coverage multiplier
        """
        insurance_info = self.tax_data.get('insurance_estimate', {})
        homeowners = insurance_info.get('homeowners', insurance_info)  # Support nested or flat structure

        # Get base rate - try enhanced schema first
        avg_rate_per_1000 = homeowners.get('avg_rate_per_1000')
        if avg_rate_per_1000 is not None:
            # Enhanced schema: rate per $1000
            rate = Decimal(str(avg_rate_per_1000))
            dwelling_coverage_multiplier = Decimal(str(homeowners.get('dwelling_coverage_multiplier', 1.0)))
            dwelling_coverage = property_value * dwelling_coverage_multiplier
            base_premium = (dwelling_coverage / Decimal('1000')) * rate
        else:
            # Legacy schema: premium per $100k
            base_premium_per_100k = Decimal(str(homeowners.get('base_premium_per_100k', 650)))
            base_premium = (property_value / Decimal('100000')) * base_premium_per_100k

        # Apply risk modifiers if available
        risk_modifiers = homeowners.get('risk_modifiers', {})
        risk_multiplier = Decimal('1.0')

        if risk_factors and risk_modifiers:
            for risk_type, has_risk in risk_factors.items():
                if has_risk and risk_type in risk_modifiers:
                    # Add the modifier (e.g., 0.15 = 15% increase)
                    modifier_value = Decimal(str(risk_modifiers[risk_type]))
                    risk_multiplier += modifier_value

        annual_premium = base_premium * risk_multiplier

        return annual_premium.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _calculate_recording_fees(self) -> Decimal:
        """Calculate total recording fees from scraped data"""
        recording_fees = self.tax_data.get('recording_fees', {})

        # Deed recording
        deed_flat = Decimal(str(recording_fees.get('deed', {}).get('flat', 50)))
        deed_pages = 3  # Typical deed length
        deed_per_page = Decimal(str(recording_fees.get('deed', {}).get('per_page', 5)))
        deed_total = deed_flat + (deed_per_page * deed_pages)

        # Mortgage recording
        mortgage_flat = Decimal(str(recording_fees.get('mortgage', {}).get('flat', 80)))
        mortgage_pages = 10  # Typical mortgage length
        mortgage_per_page = Decimal(str(recording_fees.get('mortgage', {}).get('per_page', 5)))
        mortgage_total = mortgage_flat + (mortgage_per_page * mortgage_pages)

        # Surcharges
        surcharge = Decimal(str(recording_fees.get('surcharge', 20)))

        total = deed_total + mortgage_total + surcharge

        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _calculate_transfer_taxes(
        self,
        property_value: Decimal,
        first_time_homebuyer: bool
    ) -> Decimal:
        """
        Calculate transfer taxes from scraped data with buyer/seller split

        Applies first-time homebuyer exemptions if applicable
        Enhanced schema supports explicit payer_split ratios
        """
        transfer_tax = self.tax_data.get('transfer_tax', {})

        state_rate = Decimal(str(transfer_tax.get('state_rate', 0.005)))
        county_rate = Decimal(str(transfer_tax.get('county_rate', 0.01)))

        # Check first-time homebuyer exemption
        if first_time_homebuyer:
            ftb_threshold = Decimal(str(transfer_tax.get('first_time_buyer_threshold', 0)))
            ftb_info = transfer_tax.get('first_time_buyer', {})

            if ftb_threshold > 0 and property_value <= ftb_threshold:
                # Enhanced schema: use effective_state_rate if available
                effective_rate = ftb_info.get('effective_state_rate')
                if effective_rate is not None:
                    state_rate = Decimal(str(effective_rate))
                else:
                    # Legacy: check exemption text
                    exemption = transfer_tax.get('first_time_buyer_exemption', '')
                    if 'state portion waived' in exemption.lower():
                        state_rate = Decimal('0')

                # Use FTB payer split override if available
                ftb_split = ftb_info.get('payer_split_override', {})
                if ftb_split:
                    buyer_portion_ftb = Decimal(str(ftb_split.get('buyer', 0.0)))
                    seller_portion_ftb = Decimal(str(ftb_split.get('seller', 1.0)))
                else:
                    buyer_portion_ftb = None
                    seller_portion_ftb = None
            else:
                buyer_portion_ftb = None
                seller_portion_ftb = None
        else:
            buyer_portion_ftb = None
            seller_portion_ftb = None

        # Calculate taxes
        state_tax = property_value * state_rate
        county_tax = property_value * county_rate

        # Determine buyer/seller split
        if buyer_portion_ftb is not None:
            # FTB override
            buyer_portion = buyer_portion_ftb
        else:
            # Standard split from payer_split
            payer_split = transfer_tax.get('payer_split', {})
            if payer_split:
                buyer_portion = Decimal(str(payer_split.get('buyer', 0.5)))
            else:
                # Legacy: parse split_rule text
                split_rule = transfer_tax.get('buyer_seller_split', 'seller pays')
                if 'negotiable' in split_rule.lower() or 'buyer pays' in split_rule.lower():
                    buyer_portion = Decimal('0.5')  # Assume 50/50 if negotiable
                else:
                    buyer_portion = Decimal('0')  # Seller typically pays

        total_buyer = (state_tax + county_tax) * buyer_portion

        return total_buyer.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _calculate_recordation_taxes(self, property_value: Decimal) -> Decimal:
        """
        Calculate recordation taxes with tiered structure

        Enhanced schema uses rate_per_500 (rate per $500 increment)
        Legacy schema uses percentage rates
        """
        from math import ceil

        recordation_tax = self.tax_data.get('recordation_tax', {})
        tiers = recordation_tax.get('tiers', [])

        if not tiers:
            # Flat rate if no tiers
            rate = Decimal(str(recordation_tax.get('rate', 0.0035)))
            return (property_value * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Calculate with tiers
        total_tax = Decimal('0')
        remaining = property_value

        for tier in tiers:
            min_value = Decimal(str(tier.get('min_value', 0)))
            max_value_raw = tier.get('max_value')

            # Check for rate_per_500 (enhanced schema)
            rate_per_500 = tier.get('rate_per_500')

            if rate_per_500 is not None:
                # Enhanced schema: calculate using $500 increments
                rate_per_500 = Decimal(str(rate_per_500))

                if max_value_raw is None:
                    # No max, apply to all remaining
                    taxable = remaining
                else:
                    max_value = Decimal(str(max_value_raw))
                    if remaining + min_value <= max_value:
                        taxable = remaining
                    else:
                        taxable = max_value - min_value

                # Calculate number of $500 increments (round up)
                increments = ceil(float(taxable / 500))
                tier_tax = Decimal(increments) * rate_per_500
                total_tax += tier_tax
                remaining -= taxable

                if remaining <= 0:
                    break
            else:
                # Legacy schema: percentage rate
                if max_value_raw is None:
                    max_value = Decimal('inf')
                else:
                    max_value = Decimal(str(max_value_raw))

                rate = Decimal(str(tier.get('rate', 0)))

                if property_value >= min_value:
                    # Calculate taxable amount in this tier
                    if property_value <= max_value:
                        taxable = property_value - min_value
                    else:
                        taxable = max_value - min_value

                    tier_tax = taxable * rate
                    total_tax += tier_tax

        # Add school increment if included (enhanced schema)
        school_increment = recordation_tax.get('school_increment', {})
        if school_increment.get('included'):
            school_rate_per_500 = Decimal(str(school_increment.get('rate_per_500', 0.5)))
            school_increments = ceil(float(property_value / 500))
            total_tax += Decimal(school_increments) * school_rate_per_500

        return total_tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _calculate_property_tax_proration(
        self,
        annual_tax: Decimal,
        closing_date: datetime
    ) -> Dict[str, Any]:
        """
        Calculate property tax proration based on closing date

        Determines how much seller owes buyer or vice versa
        based on tax billing schedule
        """
        tax_info = self.tax_data.get('property_tax', {})
        billing_schedule = tax_info.get('billing_schedule', {})

        # Get bill due dates
        first_half_due = billing_schedule.get('first_half_due', 'September 30')
        second_half_due = billing_schedule.get('second_half_due', 'December 31')

        # Daily tax amount
        daily_tax = annual_tax / Decimal('365')

        # Determine tax period and calculate proration
        # This is simplified - real implementation would need more complex logic
        # based on actual billing schedules

        # For now, calculate from January 1 to closing date
        # Convert datetime to date if needed
        closing_date_obj = closing_date.date() if hasattr(closing_date, 'date') else closing_date
        from datetime import date
        jan_1 = date(closing_date_obj.year, 1, 1)
        days_seller_owned = (closing_date_obj - jan_1).days

        seller_owes = daily_tax * days_seller_owned

        return {
            'seller_owes_buyer': float(seller_owes),
            'daily_tax_amount': float(daily_tax),
            'days_seller_owned': days_seller_owned,
            'closing_date': closing_date_obj.strftime('%Y-%m-%d'),
        }

    def _calculate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary totals across all sections"""
        return {
            'monthly_payment': results['section_b']['estimated_total_monthly_payment'],
            'cash_to_close': results['section_c']['cash_to_close'],
            'total_closing_costs': results['section_c']['closing_costs_subtotal'],
            'loan_amount': results['section_a']['loan_amount'],
            'interest_rate': results['section_a']['interest_rate'],
        }
