"""
Transfer Tax Calculator with Conditional Logic

Handles 4 scenarios:
1. New construction → Buyer pays 100% (transfer taxes + recording fees + state taxes)
2. Resale → 50/50 split (transfer taxes + recording fees)
3. Resale + first-time buyer → Exempt from state transfer taxes
4. New construction + first-time buyer → Still pays 100%

Created by: Neumann Rashid AI Development
Date: November 8, 2025
"""

from decimal import Decimal
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class TransferTaxBreakdown:
    """Complete breakdown of transfer taxes and fees"""
    # Transfer taxes
    state_transfer_tax: Decimal
    county_transfer_tax: Decimal
    total_transfer_tax: Decimal

    # Recording fees
    deed_recording_fee: Decimal
    mortgage_recording_fee: Decimal
    surcharge_fees: Decimal
    total_recording_fees: Decimal

    # Recordation taxes (MD-specific)
    recordation_tax: Decimal

    # Splits
    buyer_responsibility: Decimal
    seller_responsibility: Decimal

    # Exemptions
    first_time_buyer_exemption: Decimal

    # Totals
    total_closing_costs: Decimal
    buyer_total: Decimal
    seller_total: Decimal

    # Metadata
    scenario: str
    exemptions_applied: list


class TransferTaxCalculator:
    """
    Calculate transfer taxes and fees based on property type and buyer status.

    Scenarios:
    1. New Construction: Buyer pays 100%
    2. Resale: 50/50 split
    3. Resale + First-Time Buyer: Exempt from state transfer tax
    4. New Construction + First-Time Buyer: Still pays 100%
    """

    def __init__(
        self,
        state_transfer_rate: Decimal = Decimal('0.005'),  # 0.5% default MD
        county_transfer_rate: Decimal = Decimal('0.01'),  # 1.0% default MD
        deed_recording_base: Decimal = Decimal('50'),
        deed_recording_per_page: Decimal = Decimal('5'),
        mortgage_recording_base: Decimal = Decimal('80'),
        mortgage_recording_per_page: Decimal = Decimal('5'),
        surcharge_fee: Decimal = Decimal('20'),
        recordation_tax_rate: Decimal = Decimal('0.005'),  # 0.5% MD
        first_time_buyer_threshold: Optional[Decimal] = None,  # Max home value for exemption
    ):
        """
        Initialize transfer tax calculator.

        Args:
            state_transfer_rate: State transfer tax rate (e.g., 0.005 = 0.5%)
            county_transfer_rate: County transfer tax rate (e.g., 0.01 = 1.0%)
            deed_recording_base: Base fee for deed recording
            deed_recording_per_page: Fee per page for deed
            mortgage_recording_base: Base fee for mortgage recording
            mortgage_recording_per_page: Fee per page for mortgage
            surcharge_fee: Additional surcharges
            recordation_tax_rate: Recordation tax rate (MD-specific)
            first_time_buyer_threshold: Max home value for first-time buyer exemption
        """
        self.state_transfer_rate = state_transfer_rate
        self.county_transfer_rate = county_transfer_rate
        self.deed_recording_base = deed_recording_base
        self.deed_recording_per_page = deed_recording_per_page
        self.mortgage_recording_base = mortgage_recording_base
        self.mortgage_recording_per_page = mortgage_recording_per_page
        self.surcharge_fee = surcharge_fee
        self.recordation_tax_rate = recordation_tax_rate
        self.first_time_buyer_threshold = first_time_buyer_threshold

    def calculate(
        self,
        sales_price: Decimal,
        is_new_construction: bool,
        is_first_time_buyer: bool,
        deed_pages: int = 10,
        mortgage_pages: int = 15,
    ) -> TransferTaxBreakdown:
        """
        Calculate transfer taxes and fees based on scenario.

        Args:
            sales_price: Property sales price
            is_new_construction: True if new construction, False if resale
            is_first_time_buyer: True if first-time home buyer
            deed_pages: Number of pages in deed (for recording fees)
            mortgage_pages: Number of pages in mortgage (for recording fees)

        Returns:
            TransferTaxBreakdown with complete cost breakdown
        """
        # Calculate base transfer taxes
        state_transfer_tax = sales_price * self.state_transfer_rate
        county_transfer_tax = sales_price * self.county_transfer_rate
        total_transfer_tax = state_transfer_tax + county_transfer_tax

        # Calculate recording fees
        deed_recording_fee = (
            self.deed_recording_base +
            (deed_pages * self.deed_recording_per_page)
        )
        mortgage_recording_fee = (
            self.mortgage_recording_base +
            (mortgage_pages * self.mortgage_recording_per_page)
        )
        surcharge_fees = self.surcharge_fee
        total_recording_fees = (
            deed_recording_fee +
            mortgage_recording_fee +
            surcharge_fees
        )

        # Calculate recordation tax (MD-specific, applied to mortgage amount)
        # For simplicity, assume mortgage = 80% of sales price
        mortgage_amount = sales_price * Decimal('0.8')
        recordation_tax = mortgage_amount * self.recordation_tax_rate

        # Initialize exemptions
        exemptions_applied = []
        first_time_buyer_exemption = Decimal('0')

        # Determine scenario and calculate splits
        if is_new_construction:
            # Scenarios 1 & 4: New Construction
            # Buyer pays 100% regardless of first-time buyer status
            scenario = "New Construction"
            if is_first_time_buyer:
                scenario += " (First-Time Buyer - No Exemption)"
                exemptions_applied.append("Note: First-time buyer exemption does NOT apply to new construction")

            buyer_responsibility = Decimal('100')  # 100%
            seller_responsibility = Decimal('0')   # 0%

        else:
            # Scenarios 2 & 3: Resale
            if is_first_time_buyer:
                # Scenario 3: Resale + First-Time Buyer
                scenario = "Resale (First-Time Buyer - State Transfer Tax Exempt)"

                # Check if qualifies for exemption
                if self.first_time_buyer_threshold and sales_price > self.first_time_buyer_threshold:
                    exemptions_applied.append(
                        f"Property value ${sales_price:,.2f} exceeds first-time buyer threshold "
                        f"${self.first_time_buyer_threshold:,.2f} - partial exemption"
                    )
                    # Partial exemption based on threshold
                    exemption_ratio = self.first_time_buyer_threshold / sales_price
                    first_time_buyer_exemption = state_transfer_tax * exemption_ratio
                else:
                    # Full exemption
                    first_time_buyer_exemption = state_transfer_tax
                    exemptions_applied.append(
                        f"State transfer tax waived: ${state_transfer_tax:,.2f} saved"
                    )

                # Apply exemption
                state_transfer_tax -= first_time_buyer_exemption
                total_transfer_tax = state_transfer_tax + county_transfer_tax

                # 50/50 split on remaining
                buyer_responsibility = Decimal('50')  # 50%
                seller_responsibility = Decimal('50') # 50%

            else:
                # Scenario 2: Resale (Standard)
                scenario = "Resale (50/50 Split)"
                buyer_responsibility = Decimal('50')  # 50%
                seller_responsibility = Decimal('50') # 50%

        # Calculate actual dollar amounts for buyer and seller
        buyer_transfer_tax = total_transfer_tax * (buyer_responsibility / 100)
        seller_transfer_tax = total_transfer_tax * (seller_responsibility / 100)

        # Buyer pays recording fees and recordation tax
        buyer_recording_costs = total_recording_fees + recordation_tax

        # Calculate totals
        buyer_total = buyer_transfer_tax + buyer_recording_costs
        seller_total = seller_transfer_tax
        total_closing_costs = buyer_total + seller_total

        return TransferTaxBreakdown(
            # Transfer taxes
            state_transfer_tax=state_transfer_tax,
            county_transfer_tax=county_transfer_tax,
            total_transfer_tax=total_transfer_tax,

            # Recording fees
            deed_recording_fee=deed_recording_fee,
            mortgage_recording_fee=mortgage_recording_fee,
            surcharge_fees=surcharge_fees,
            total_recording_fees=total_recording_fees,

            # Recordation tax
            recordation_tax=recordation_tax,

            # Splits
            buyer_responsibility=buyer_responsibility,
            seller_responsibility=seller_responsibility,

            # Exemptions
            first_time_buyer_exemption=first_time_buyer_exemption,

            # Totals
            total_closing_costs=total_closing_costs,
            buyer_total=buyer_total,
            seller_total=seller_total,

            # Metadata
            scenario=scenario,
            exemptions_applied=exemptions_applied,
        )

    def get_breakdown_summary(self, breakdown: TransferTaxBreakdown) -> Dict:
        """
        Get human-readable summary of transfer tax breakdown.

        Args:
            breakdown: TransferTaxBreakdown object

        Returns:
            Dict with formatted breakdown
        """
        return {
            "scenario": breakdown.scenario,
            "transfer_taxes": {
                "state": float(breakdown.state_transfer_tax),
                "county": float(breakdown.county_transfer_tax),
                "total": float(breakdown.total_transfer_tax),
            },
            "recording_fees": {
                "deed": float(breakdown.deed_recording_fee),
                "mortgage": float(breakdown.mortgage_recording_fee),
                "surcharges": float(breakdown.surcharge_fees),
                "total": float(breakdown.total_recording_fees),
            },
            "recordation_tax": float(breakdown.recordation_tax),
            "responsibility_split": {
                "buyer_percent": float(breakdown.buyer_responsibility),
                "seller_percent": float(breakdown.seller_responsibility),
            },
            "costs": {
                "buyer": float(breakdown.buyer_total),
                "seller": float(breakdown.seller_total),
                "total": float(breakdown.total_closing_costs),
            },
            "exemptions": {
                "first_time_buyer_savings": float(breakdown.first_time_buyer_exemption),
                "applied": breakdown.exemptions_applied,
            }
        }


def example_usage():
    """Demonstrate all 4 scenarios"""

    calculator = TransferTaxCalculator(
        state_transfer_rate=Decimal('0.005'),   # 0.5% MD state
        county_transfer_rate=Decimal('0.01'),    # 1.0% MD county (Montgomery)
        first_time_buyer_threshold=Decimal('500000')  # $500k threshold
    )

    sales_price = Decimal('400000')

    scenarios = [
        {
            "name": "Scenario 1: New Construction",
            "is_new_construction": True,
            "is_first_time_buyer": False,
        },
        {
            "name": "Scenario 2: Resale (Standard)",
            "is_new_construction": False,
            "is_first_time_buyer": False,
        },
        {
            "name": "Scenario 3: Resale (First-Time Buyer)",
            "is_new_construction": False,
            "is_first_time_buyer": True,
        },
        {
            "name": "Scenario 4: New Construction (First-Time Buyer)",
            "is_new_construction": True,
            "is_first_time_buyer": True,
        },
    ]

    print("=" * 80)
    print(f"TRANSFER TAX CALCULATOR - All Scenarios")
    print(f"Sales Price: ${sales_price:,.2f}")
    print("=" * 80)

    for scenario in scenarios:
        print(f"\n{scenario['name']}")
        print("-" * 80)

        breakdown = calculator.calculate(
            sales_price=sales_price,
            is_new_construction=scenario['is_new_construction'],
            is_first_time_buyer=scenario['is_first_time_buyer'],
        )

        summary = calculator.get_breakdown_summary(breakdown)

        print(f"Scenario Type: {summary['scenario']}")
        print(f"\nTransfer Taxes:")
        print(f"  State:  ${summary['transfer_taxes']['state']:>10,.2f}")
        print(f"  County: ${summary['transfer_taxes']['county']:>10,.2f}")
        print(f"  Total:  ${summary['transfer_taxes']['total']:>10,.2f}")

        print(f"\nRecording Fees:")
        print(f"  Deed:       ${summary['recording_fees']['deed']:>10,.2f}")
        print(f"  Mortgage:   ${summary['recording_fees']['mortgage']:>10,.2f}")
        print(f"  Surcharges: ${summary['recording_fees']['surcharges']:>10,.2f}")
        print(f"  Total:      ${summary['recording_fees']['total']:>10,.2f}")

        print(f"\nRecordation Tax: ${summary['recordation_tax']:>10,.2f}")

        print(f"\nResponsibility:")
        print(f"  Buyer:  {summary['responsibility_split']['buyer_percent']:>5.0f}%")
        print(f"  Seller: {summary['responsibility_split']['seller_percent']:>5.0f}%")

        print(f"\nTotal Costs:")
        print(f"  Buyer:  ${summary['costs']['buyer']:>10,.2f}")
        print(f"  Seller: ${summary['costs']['seller']:>10,.2f}")
        print(f"  Total:  ${summary['costs']['total']:>10,.2f}")

        if summary['exemptions']['first_time_buyer_savings'] > 0:
            print(f"\n💰 First-Time Buyer Savings: ${summary['exemptions']['first_time_buyer_savings']:,.2f}")

        if summary['exemptions']['applied']:
            print(f"\nExemptions Applied:")
            for exemption in summary['exemptions']['applied']:
                print(f"  • {exemption}")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    example_usage()
