"""
Fee Engine - Deterministic fee calculations with source tracking

Centralizes all fee calculations with:
- Deterministic results (same inputs = same outputs)
- Source badges (system/AI/override)
- JSON trace for audit
- Jurisdiction DB integration

Handles:
- Transfer taxes (state/county)
- Recording fees (deed/mortgage)
- Recordation taxes (tiered)
- Title fees (search/insurance)
- Prepaids (insurance/taxes)
- Escrows (RESPA-compliant)
- UFMIP (FHA upfront MIP)
- MIP (FHA annual)
- VAFF (VA funding fee)
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from math import ceil
import logging

logger = logging.getLogger(__name__)


# Source constants
SOURCE_SYSTEM = "system"
SOURCE_AI = "ai"
SOURCE_OVERRIDE = "override"


@dataclass
class FeeLineItem:
    """Single fee line item with source tracking"""
    category: str  # e.g., "transfer_tax", "recording_fee", "title", "prepaid", "escrow", "mip"
    subcategory: str  # e.g., "state", "county", "deed", "mortgage", "lender", "owner"
    description: str
    amount: Decimal
    source: str  # "system", "ai", "override"
    source_detail: str  # e.g., "TaxData v2.0 (MD-Montgomery)", "User override", "FHA guidelines"
    calculation_trace: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        result = asdict(self)
        result['amount'] = float(self.amount)
        return result


@dataclass
class FeeCalculationResult:
    """Complete fee calculation with all line items and audit trail"""
    # Line items grouped by category
    transfer_taxes: List[FeeLineItem] = field(default_factory=list)
    recording_fees: List[FeeLineItem] = field(default_factory=list)
    recordation_taxes: List[FeeLineItem] = field(default_factory=list)
    title_fees: List[FeeLineItem] = field(default_factory=list)
    prepaids: List[FeeLineItem] = field(default_factory=list)
    escrows: List[FeeLineItem] = field(default_factory=list)
    mortgage_insurance: List[FeeLineItem] = field(default_factory=list)

    # Totals
    total_transfer_taxes: Decimal = Decimal('0')
    total_recording_fees: Decimal = Decimal('0')
    total_recordation_taxes: Decimal = Decimal('0')
    total_title_fees: Decimal = Decimal('0')
    total_prepaids: Decimal = Decimal('0')
    total_escrows: Decimal = Decimal('0')
    total_mortgage_insurance: Decimal = Decimal('0')
    total_fees: Decimal = Decimal('0')

    # Metadata
    jurisdiction: str = ""
    tax_data_version: str = ""
    calculation_timestamp: str = ""
    deterministic_hash: str = ""  # Hash of inputs for determinism verification

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'transfer_taxes': [item.to_dict() for item in self.transfer_taxes],
            'recording_fees': [item.to_dict() for item in self.recording_fees],
            'recordation_taxes': [item.to_dict() for item in self.recordation_taxes],
            'title_fees': [item.to_dict() for item in self.title_fees],
            'prepaids': [item.to_dict() for item in self.prepaids],
            'escrows': [item.to_dict() for item in self.escrows],
            'mortgage_insurance': [item.to_dict() for item in self.mortgage_insurance],
            'total_transfer_taxes': float(self.total_transfer_taxes),
            'total_recording_fees': float(self.total_recording_fees),
            'total_recordation_taxes': float(self.total_recordation_taxes),
            'total_title_fees': float(self.total_title_fees),
            'total_prepaids': float(self.total_prepaids),
            'total_escrows': float(self.total_escrows),
            'total_mortgage_insurance': float(self.total_mortgage_insurance),
            'total_fees': float(self.total_fees),
            'jurisdiction': self.jurisdiction,
            'tax_data_version': self.tax_data_version,
            'calculation_timestamp': self.calculation_timestamp,
            'deterministic_hash': self.deterministic_hash,
        }


class FeeEngine:
    """
    Deterministic fee calculation engine with jurisdiction DB integration
    """

    def __init__(self, tax_data: Dict[str, Any], tax_data_version: str = "2.0"):
        """
        Initialize fee engine with jurisdiction tax data

        Args:
            tax_data: Tax data from TaxData model (JSON field)
            tax_data_version: Schema version (e.g., "2.0")
        """
        self.tax_data = tax_data
        self.tax_data_version = tax_data_version
        self.overrides: Dict[str, Any] = {}

    def calculate_all_fees(
        self,
        property_value: Decimal,
        loan_amount: Decimal,
        loan_type: str = 'conventional',
        first_time_homebuyer: bool = False,
        is_new_construction: bool = False,
        closing_date: Optional[date] = None,
        zip_code: Optional[str] = None,
        down_payment_pct: Decimal = Decimal('20'),
        disabled_veteran: bool = False,
        first_va_use: bool = True,
    ) -> FeeCalculationResult:
        """
        Calculate all fees with deterministic results and source tracking

        Args:
            property_value: Property purchase price
            loan_amount: Mortgage loan amount
            loan_type: 'conventional', 'fha', 'va'
            first_time_homebuyer: First-time buyer status
            is_new_construction: New construction property
            closing_date: Loan closing date
            zip_code: Property ZIP code
            down_payment_pct: Down payment percentage
            disabled_veteran: Disabled veteran status (VA only)
            first_va_use: First VA loan use (VA only)

        Returns:
            FeeCalculationResult with all line items and totals
        """
        result = FeeCalculationResult()
        result.calculation_timestamp = datetime.now().isoformat()
        result.tax_data_version = self.tax_data_version

        # Generate deterministic hash of inputs
        result.deterministic_hash = self._generate_deterministic_hash({
            'property_value': float(property_value),
            'loan_amount': float(loan_amount),
            'loan_type': loan_type,
            'first_time_homebuyer': first_time_homebuyer,
            'is_new_construction': is_new_construction,
            'closing_date': closing_date.isoformat() if closing_date else None,
            'zip_code': zip_code,
            'down_payment_pct': float(down_payment_pct),
        })

        # Calculate each fee category
        self._calculate_transfer_taxes(result, property_value, first_time_homebuyer, is_new_construction)
        self._calculate_recording_fees(result, property_value, loan_amount)
        self._calculate_recordation_taxes(result, loan_amount)
        self._calculate_title_fees(result, property_value, loan_amount)
        self._calculate_prepaids(result, property_value, closing_date or date.today())
        self._calculate_escrows(result, property_value, closing_date or date.today(), zip_code)
        self._calculate_mortgage_insurance(
            result, loan_amount, property_value, loan_type,
            down_payment_pct, disabled_veteran, first_va_use
        )

        # Calculate totals
        result.total_transfer_taxes = sum((item.amount for item in result.transfer_taxes), Decimal('0'))
        result.total_recording_fees = sum((item.amount for item in result.recording_fees), Decimal('0'))
        result.total_recordation_taxes = sum((item.amount for item in result.recordation_taxes), Decimal('0'))
        result.total_title_fees = sum((item.amount for item in result.title_fees), Decimal('0'))
        result.total_prepaids = sum((item.amount for item in result.prepaids), Decimal('0'))
        result.total_escrows = sum((item.amount for item in result.escrows), Decimal('0'))
        result.total_mortgage_insurance = sum((item.amount for item in result.mortgage_insurance), Decimal('0'))
        result.total_fees = (
            result.total_transfer_taxes +
            result.total_recording_fees +
            result.total_recordation_taxes +
            result.total_title_fees +
            result.total_prepaids +
            result.total_escrows +
            result.total_mortgage_insurance
        )

        # Set jurisdiction for audit
        state = self.tax_data.get('state', 'Unknown')
        county = self.tax_data.get('county', 'Unknown')
        result.jurisdiction = f"{state}-{county}"

        return result

    def _calculate_transfer_taxes(
        self,
        result: FeeCalculationResult,
        property_value: Decimal,
        first_time_homebuyer: bool,
        is_new_construction: bool
    ):
        """Calculate state and county transfer taxes with FTB exemptions"""
        transfer_tax_data = self.tax_data.get('transfer_tax', {})

        state_rate = Decimal(str(transfer_tax_data.get('state_rate', 0.005)))
        county_rate = Decimal(str(transfer_tax_data.get('county_rate', 0.01)))

        # Calculate base taxes
        state_tax = property_value * state_rate
        county_tax = property_value * county_rate

        # Source tracking
        source = SOURCE_SYSTEM if self.tax_data.get('sources') else SOURCE_AI
        source_detail = f"TaxData v{self.tax_data_version} ({result.jurisdiction})"

        # Determine buyer/seller split first
        if is_new_construction:
            buyer_portion = Decimal('1.0')  # Buyer pays 100%
        else:
            payer_split = transfer_tax_data.get('payer_split', {})
            buyer_portion = Decimal(str(payer_split.get('buyer', 0.5)))

        # Calculate buyer's share
        state_tax_buyer = state_tax * buyer_portion
        county_tax_buyer = county_tax * buyer_portion

        # Check for first-time homebuyer exemption
        exemption_amount = Decimal('0')
        if first_time_homebuyer and not is_new_construction:
            ftb_threshold = Decimal(str(transfer_tax_data.get('first_time_buyer_threshold', 0)))
            ftb_info = transfer_tax_data.get('first_time_buyer', {})

            if ftb_threshold > 0 and property_value <= ftb_threshold:
                effective_rate = ftb_info.get('effective_state_rate', 0)
                if effective_rate == 0:
                    # Mark exemption amount (will be added as negative line item)
                    exemption_amount = state_tax_buyer

        # Add state transfer tax line item (always show, even if will be offset by exemption)
        if state_tax_buyer > 0:
            result.transfer_taxes.append(FeeLineItem(
                category="transfer_tax",
                subcategory="state",
                description=f"State Transfer Tax ({float(state_rate)*100:.2f}%, {float(buyer_portion)*100:.0f}% buyer)",
                amount=state_tax_buyer.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                source=source,
                source_detail=source_detail,
                calculation_trace={
                    'property_value': float(property_value),
                    'rate': float(state_rate),
                    'base_tax': float(state_tax_buyer / buyer_portion),
                    'buyer_portion': float(buyer_portion),
                    'exemption_applied': float(exemption_amount),
                }
            ))

        # Add county transfer tax line item
        if county_tax_buyer > 0:
            result.transfer_taxes.append(FeeLineItem(
                category="transfer_tax",
                subcategory="county",
                description=f"County Transfer Tax ({float(county_rate)*100:.2f}%, {float(buyer_portion)*100:.0f}% buyer)",
                amount=county_tax_buyer.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                source=source,
                source_detail=source_detail,
                calculation_trace={
                    'property_value': float(property_value),
                    'rate': float(county_rate),
                    'base_tax': float(county_tax_buyer / buyer_portion),
                    'buyer_portion': float(buyer_portion),
                }
            ))

        # Add exemption note if applicable
        if exemption_amount > 0:
            result.transfer_taxes.append(FeeLineItem(
                category="transfer_tax",
                subcategory="exemption",
                description="First-Time Homebuyer Exemption (State Transfer Tax)",
                amount=-exemption_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                source=source,
                source_detail=source_detail,
                calculation_trace={'exemption_amount': float(exemption_amount)}
            ))

    def _calculate_recording_fees(
        self,
        result: FeeCalculationResult,
        property_value: Decimal,
        loan_amount: Decimal
    ):
        """Calculate deed and mortgage recording fees"""
        recording_data = self.tax_data.get('recording_fees', {})

        # Deed recording
        deed_data = recording_data.get('deed', {})
        deed_base = Decimal(str(deed_data.get('base', 50)))
        deed_per_page = Decimal(str(deed_data.get('per_page', 5)))
        deed_pages = deed_data.get('typical_pages', 3)
        deed_total = deed_base + (deed_per_page * deed_pages)

        # Mortgage recording
        mortgage_data = recording_data.get('mortgage', {})
        mortgage_base = Decimal(str(mortgage_data.get('base', 80)))
        mortgage_per_page = Decimal(str(mortgage_data.get('per_page', 5)))
        mortgage_pages = mortgage_data.get('typical_pages', 10)
        mortgage_total = mortgage_base + (mortgage_per_page * mortgage_pages)

        # Surcharges
        surcharge = Decimal(str(recording_data.get('surcharge', 20)))
        tech_fee = Decimal(str(recording_data.get('tech_fee', 0)))

        source = SOURCE_SYSTEM if self.tax_data.get('sources') else SOURCE_AI
        source_detail = f"TaxData v{self.tax_data_version}"

        result.recording_fees.append(FeeLineItem(
            category="recording_fee",
            subcategory="deed",
            description=f"Deed Recording ({deed_pages} pages)",
            amount=deed_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            source=source,
            source_detail=source_detail,
            calculation_trace={
                'base': float(deed_base),
                'per_page': float(deed_per_page),
                'pages': deed_pages,
            }
        ))

        result.recording_fees.append(FeeLineItem(
            category="recording_fee",
            subcategory="mortgage",
            description=f"Mortgage Recording ({mortgage_pages} pages)",
            amount=mortgage_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            source=source,
            source_detail=source_detail,
            calculation_trace={
                'base': float(mortgage_base),
                'per_page': float(mortgage_per_page),
                'pages': mortgage_pages,
            }
        ))

        if surcharge > 0:
            result.recording_fees.append(FeeLineItem(
                category="recording_fee",
                subcategory="surcharge",
                description="Recording Surcharge",
                amount=surcharge.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                source=source,
                source_detail=source_detail,
                calculation_trace={'surcharge': float(surcharge)}
            ))

        if tech_fee > 0:
            result.recording_fees.append(FeeLineItem(
                category="recording_fee",
                subcategory="tech_fee",
                description="Technology Fee",
                amount=tech_fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                source=source,
                source_detail=source_detail,
                calculation_trace={'tech_fee': float(tech_fee)}
            ))

    def _calculate_recordation_taxes(
        self,
        result: FeeCalculationResult,
        loan_amount: Decimal
    ):
        """Calculate tiered recordation taxes (MD-specific)"""
        recordation_data = self.tax_data.get('recordation_tax', {})
        tiers = recordation_data.get('tiers', [])

        if not tiers:
            # Flat rate if no tiers
            rate = Decimal(str(recordation_data.get('rate', 0)))
            if rate > 0:
                tax = loan_amount * rate
                result.recordation_taxes.append(FeeLineItem(
                    category="recordation_tax",
                    subcategory="base",
                    description=f"Recordation Tax ({float(rate)*100:.2f}%)",
                    amount=tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                    source=SOURCE_SYSTEM,
                    source_detail=f"TaxData v{self.tax_data_version}",
                    calculation_trace={'loan_amount': float(loan_amount), 'rate': float(rate)}
                ))
            return

        # Calculate with tiers
        total_tax = Decimal('0')
        remaining = loan_amount
        trace = []

        for tier in tiers:
            min_value = Decimal(str(tier.get('min_value', 0)))
            max_value_raw = tier.get('max_value')
            rate_per_500 = tier.get('rate_per_500')

            if rate_per_500 is not None:
                rate_per_500 = Decimal(str(rate_per_500))

                if max_value_raw is None:
                    taxable = remaining
                else:
                    max_value = Decimal(str(max_value_raw))
                    taxable = min(remaining, max_value - min_value)

                increments = ceil(float(taxable / 500))
                tier_tax = Decimal(increments) * rate_per_500
                total_tax += tier_tax
                remaining -= taxable

                trace.append({
                    'min_value': float(min_value),
                    'max_value': float(max_value_raw) if max_value_raw else None,
                    'taxable_amount': float(taxable),
                    'rate_per_500': float(rate_per_500),
                    'increments': increments,
                    'tier_tax': float(tier_tax),
                })

                if remaining <= 0:
                    break

        # Add school increment if included
        school_increment = recordation_data.get('school_increment', {})
        if school_increment.get('included'):
            school_rate_per_500 = Decimal(str(school_increment.get('rate_per_500', 0.5)))
            school_increments = ceil(float(loan_amount / 500))
            school_tax = Decimal(school_increments) * school_rate_per_500
            total_tax += school_tax

            trace.append({
                'school_increment': True,
                'rate_per_500': float(school_rate_per_500),
                'increments': school_increments,
                'school_tax': float(school_tax),
            })

        if total_tax > 0:
            result.recordation_taxes.append(FeeLineItem(
                category="recordation_tax",
                subcategory="tiered",
                description="Recordation Tax (Tiered)",
                amount=total_tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                source=SOURCE_SYSTEM,
                source_detail=f"TaxData v{self.tax_data_version}",
                calculation_trace={'loan_amount': float(loan_amount), 'tiers': trace}
            ))

    def _calculate_title_fees(
        self,
        result: FeeCalculationResult,
        property_value: Decimal,
        loan_amount: Decimal
    ):
        """Calculate title search and insurance fees"""
        title_data = self.tax_data.get('title_fees', {})

        # Title search
        search_fee = Decimal(str(title_data.get('title_search', 250)))

        # Title insurance
        lender_rate_per_1000 = Decimal(str(title_data.get('lender_policy_rate_per_1000', 5)))
        owner_rate_per_1000 = Decimal(str(title_data.get('owner_policy_rate_per_1000', 5)))

        lender_insurance = (loan_amount / Decimal('1000')) * lender_rate_per_1000
        owner_insurance = (property_value / Decimal('1000')) * owner_rate_per_1000

        # Simultaneous issue discount
        sim_discount = Decimal(str(title_data.get('simultaneous_issue_discount', 0)))
        if sim_discount > 0:
            owner_insurance = owner_insurance * (Decimal('1') - sim_discount)

        source = SOURCE_SYSTEM if self.tax_data.get('sources') else SOURCE_AI
        source_detail = f"TaxData v{self.tax_data_version}"

        result.title_fees.append(FeeLineItem(
            category="title",
            subcategory="search",
            description="Title Search",
            amount=search_fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            source=source,
            source_detail=source_detail,
            calculation_trace={'search_fee': float(search_fee)}
        ))

        result.title_fees.append(FeeLineItem(
            category="title",
            subcategory="lender_insurance",
            description=f"Lender's Title Insurance (${float(lender_rate_per_1000):.2f}/$1000)",
            amount=lender_insurance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            source=source,
            source_detail=source_detail,
            calculation_trace={
                'loan_amount': float(loan_amount),
                'rate_per_1000': float(lender_rate_per_1000),
            }
        ))

        result.title_fees.append(FeeLineItem(
            category="title",
            subcategory="owner_insurance",
            description=f"Owner's Title Insurance (${float(owner_rate_per_1000):.2f}/$1000)",
            amount=owner_insurance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            source=source,
            source_detail=source_detail,
            calculation_trace={
                'property_value': float(property_value),
                'rate_per_1000': float(owner_rate_per_1000),
                'simultaneous_discount': float(sim_discount),
            }
        ))

    def _calculate_prepaids(
        self,
        result: FeeCalculationResult,
        property_value: Decimal,
        closing_date: date
    ):
        """Calculate prepaid homeowners insurance and property taxes"""
        # Homeowners insurance (typically 1 year prepaid)
        insurance_data = self.tax_data.get('insurance_estimate', {})
        homeowners = insurance_data.get('homeowners', insurance_data)

        avg_rate_per_1000 = Decimal(str(homeowners.get('avg_rate_per_1000', 6.5)))
        annual_premium = (property_value / Decimal('1000')) * avg_rate_per_1000

        result.prepaids.append(FeeLineItem(
            category="prepaid",
            subcategory="homeowners_insurance",
            description="Homeowners Insurance (1 year prepaid)",
            amount=annual_premium.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            source=SOURCE_AI,
            source_detail=f"TaxData v{self.tax_data_version} estimate",
            calculation_trace={
                'property_value': float(property_value),
                'rate_per_1000': float(avg_rate_per_1000),
            }
        ))

        # Property tax proration (prepaid to closing)
        property_tax_data = self.tax_data.get('property_tax', {})
        assessment_ratio = Decimal(str(property_tax_data.get('assessment_ratio', 100))) / 100
        composite_rate_per_100 = Decimal(str(property_tax_data.get('composite_rate_per_100', 1.0))) / 100

        assessed_value = property_value * assessment_ratio
        annual_tax = assessed_value * composite_rate_per_100
        daily_tax = annual_tax / Decimal('365')

        # Days from Jan 1 to closing
        jan_1 = date(closing_date.year, 1, 1)
        days_seller_owned = (closing_date - jan_1).days
        prepaid_tax = daily_tax * days_seller_owned

        result.prepaids.append(FeeLineItem(
            category="prepaid",
            subcategory="property_tax",
            description=f"Property Tax Proration ({days_seller_owned} days)",
            amount=prepaid_tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            source=SOURCE_SYSTEM,
            source_detail=f"TaxData v{self.tax_data_version}",
            calculation_trace={
                'annual_tax': float(annual_tax),
                'daily_tax': float(daily_tax),
                'days_seller_owned': days_seller_owned,
                'closing_date': closing_date.isoformat(),
            }
        ))

    def _calculate_escrows(
        self,
        result: FeeCalculationResult,
        property_value: Decimal,
        closing_date: date,
        zip_code: Optional[str] = None
    ):
        """Calculate RESPA-compliant initial escrow deposits"""
        escrow_rules = self.tax_data.get('escrow_rules', {})
        cushion_months = Decimal(str(escrow_rules.get('cushion_months', 2)))

        # Homeowners insurance escrow
        insurance_data = self.tax_data.get('insurance_estimate', {})
        homeowners = insurance_data.get('homeowners', insurance_data)
        avg_rate_per_1000 = Decimal(str(homeowners.get('avg_rate_per_1000', 6.5)))
        annual_premium = (property_value / Decimal('1000')) * avg_rate_per_1000
        monthly_insurance = annual_premium / 12

        insurance_escrow = monthly_insurance * cushion_months

        result.escrows.append(FeeLineItem(
            category="escrow",
            subcategory="homeowners_insurance",
            description=f"Homeowners Insurance Escrow ({int(cushion_months)} months)",
            amount=insurance_escrow.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            source=SOURCE_SYSTEM,
            source_detail="RESPA-compliant cushion",
            calculation_trace={
                'monthly_amount': float(monthly_insurance),
                'cushion_months': float(cushion_months),
            }
        ))

        # Property tax escrow (typically 3 months)
        property_tax_data = self.tax_data.get('property_tax', {})
        assessment_ratio = Decimal(str(property_tax_data.get('assessment_ratio', 100))) / 100
        composite_rate_per_100 = Decimal(str(property_tax_data.get('composite_rate_per_100', 1.0))) / 100

        assessed_value = property_value * assessment_ratio
        annual_tax = assessed_value * composite_rate_per_100
        monthly_tax = annual_tax / 12

        tax_cushion_months = Decimal('3')  # Typically 3 months for property tax
        tax_escrow = monthly_tax * tax_cushion_months

        result.escrows.append(FeeLineItem(
            category="escrow",
            subcategory="property_tax",
            description=f"Property Tax Escrow ({int(tax_cushion_months)} months)",
            amount=tax_escrow.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            source=SOURCE_SYSTEM,
            source_detail="RESPA-compliant cushion",
            calculation_trace={
                'monthly_amount': float(monthly_tax),
                'cushion_months': float(tax_cushion_months),
            }
        ))

    def _calculate_mortgage_insurance(
        self,
        result: FeeCalculationResult,
        loan_amount: Decimal,
        property_value: Decimal,
        loan_type: str,
        down_payment_pct: Decimal,
        disabled_veteran: bool,
        first_va_use: bool
    ):
        """Calculate UFMIP/MIP/VAFF based on loan type"""
        ltv = ((Decimal('100') - down_payment_pct) / Decimal('100')) * 100

        if loan_type == 'fha':
            # FHA UFMIP (Upfront Mortgage Insurance Premium)
            ufmip_rate = Decimal('1.75') / 100
            ufmip = loan_amount * ufmip_rate

            result.mortgage_insurance.append(FeeLineItem(
                category="mortgage_insurance",
                subcategory="ufmip",
                description="FHA Upfront MIP (UFMIP) - 1.75%",
                amount=ufmip.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                source=SOURCE_SYSTEM,
                source_detail="FHA guidelines (HUD 4000.1)",
                calculation_trace={
                    'loan_amount': float(loan_amount),
                    'rate': float(ufmip_rate),
                    'can_be_financed': True,
                }
            ))

            # FHA Annual MIP (monthly payment, not closing cost, but tracked)
            annual_mip_rate = Decimal('0.85') / 100 if ltv > 95 else Decimal('0.80') / 100
            # Note: Annual MIP is typically not a closing cost but a monthly payment component

        elif loan_type == 'va':
            # VA Funding Fee (VAFF)
            if disabled_veteran:
                # Waived for disabled veterans
                result.mortgage_insurance.append(FeeLineItem(
                    category="mortgage_insurance",
                    subcategory="vaff",
                    description="VA Funding Fee (Waived - Disabled Veteran)",
                    amount=Decimal('0'),
                    source=SOURCE_SYSTEM,
                    source_detail="VA guidelines - Disability waiver",
                    calculation_trace={'disabled_veteran': True, 'waived': True}
                ))
            else:
                # Calculate VA funding fee
                if down_payment_pct >= 10:
                    fee_rate = Decimal('1.4') / 100
                elif down_payment_pct >= 5:
                    fee_rate = Decimal('1.65') / 100
                else:
                    fee_rate = Decimal('2.3') / 100 if first_va_use else Decimal('3.6') / 100

                vaff = loan_amount * fee_rate

                result.mortgage_insurance.append(FeeLineItem(
                    category="mortgage_insurance",
                    subcategory="vaff",
                    description=f"VA Funding Fee - {float(fee_rate)*100:.2f}%",
                    amount=vaff.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                    source=SOURCE_SYSTEM,
                    source_detail="VA guidelines (VA Pamphlet 26-7)",
                    calculation_trace={
                        'loan_amount': float(loan_amount),
                        'rate': float(fee_rate),
                        'down_payment_pct': float(down_payment_pct),
                        'first_use': first_va_use,
                        'can_be_financed': True,
                    }
                ))

        elif loan_type == 'conventional' and ltv > 80:
            # Conventional PMI (monthly payment, not typically a closing cost)
            # Tracked for completeness but usually not included in closing costs
            pass

    def _generate_deterministic_hash(self, inputs: Dict[str, Any]) -> str:
        """Generate deterministic hash of inputs for verification"""
        import hashlib
        import json

        # Sort keys for determinism
        sorted_inputs = json.dumps(inputs, sort_keys=True)
        return hashlib.sha256(sorted_inputs.encode()).hexdigest()[:16]
