"""
Unit tests for FeeEngine - deterministic fee calculations with source tracking
"""

import unittest
from decimal import Decimal
from datetime import date
from calculator.fee_engine import (
    FeeEngine,
    FeeCalculationResult,
    FeeLineItem,
    SOURCE_SYSTEM,
    SOURCE_AI,
    SOURCE_OVERRIDE,
)


class TestFeeEngine(unittest.TestCase):
    """Test FeeEngine calculations"""

    def setUp(self):
        """Set up test data"""
        # Sample MD tax data (Maryland - Montgomery County)
        self.tax_data = {
            'state': 'MD',
            'county': 'Montgomery',
            'property_tax': {
                'assessment_ratio': 100,
                'composite_rate_per_100': 1.0,
            },
            'transfer_tax': {
                'state_rate': 0.005,  # 0.5%
                'county_rate': 0.01,  # 1.0%
                'payer_split': {'buyer': 0.5, 'seller': 0.5},
                'first_time_buyer_threshold': 500000,
                'first_time_buyer': {
                    'effective_state_rate': 0,
                }
            },
            'recording_fees': {
                'deed': {'base': 50, 'per_page': 5, 'typical_pages': 3},
                'mortgage': {'base': 80, 'per_page': 5, 'typical_pages': 10},
                'surcharge': 20,
                'tech_fee': 0,
            },
            'recordation_tax': {
                'tiers': [
                    {'min_value': 0, 'max_value': 500000, 'rate_per_500': 2.5},
                    {'min_value': 500000, 'max_value': None, 'rate_per_500': 5.0},
                ],
                'school_increment': {'included': True, 'rate_per_500': 0.5},
            },
            'title_fees': {
                'title_search': 250,
                'lender_policy_rate_per_1000': 5.0,
                'owner_policy_rate_per_1000': 5.0,
                'simultaneous_issue_discount': 0.1,
            },
            'insurance_estimate': {
                'homeowners': {
                    'avg_rate_per_1000': 6.5,
                }
            },
            'escrow_rules': {
                'cushion_months': 2,
            },
            'sources': ['https://example.com/md-tax-data'],
        }

    def test_deterministic_hash_consistency(self):
        """Test that same inputs produce same hash"""
        engine = FeeEngine(self.tax_data, "2.0")

        result1 = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('320000'),
            loan_type='conventional',
            closing_date=date(2025, 6, 15),
        )

        result2 = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('320000'),
            loan_type='conventional',
            closing_date=date(2025, 6, 15),
        )

        self.assertEqual(result1.deterministic_hash, result2.deterministic_hash)

    def test_transfer_tax_calculation_standard(self):
        """Test standard transfer tax calculation (50/50 split)"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('320000'),
            loan_type='conventional',
            first_time_homebuyer=False,
            is_new_construction=False,
        )

        # State transfer tax: $400,000 * 0.005 = $2,000 * 0.5 (buyer) = $1,000
        # County transfer tax: $400,000 * 0.01 = $4,000 * 0.5 (buyer) = $2,000
        # Total buyer: $3,000
        self.assertEqual(result.total_transfer_taxes, Decimal('3000.00'))

    def test_transfer_tax_first_time_buyer_exemption(self):
        """Test first-time buyer exemption (state transfer tax waived)"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('320000'),
            loan_type='conventional',
            first_time_homebuyer=True,
            is_new_construction=False,
        )

        # State transfer tax: $400,000 * 0.005 = $2,000 * 0.5 = $1,000 - WAIVED = $0
        # County transfer tax: $400,000 * 0.01 = $4,000 * 0.5 = $2,000
        # Total buyer: $2,000
        self.assertEqual(result.total_transfer_taxes, Decimal('2000.00'))

        # Verify exemption line item exists
        exemption_items = [
            item for item in result.transfer_taxes
            if item.subcategory == 'exemption'
        ]
        self.assertEqual(len(exemption_items), 1)
        self.assertEqual(exemption_items[0].amount, Decimal('-1000.00'))

    def test_transfer_tax_new_construction(self):
        """Test new construction (buyer pays 100%)"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('320000'),
            loan_type='conventional',
            first_time_homebuyer=False,
            is_new_construction=True,
        )

        # State transfer tax: $400,000 * 0.005 = $2,000 * 1.0 (buyer) = $2,000
        # County transfer tax: $400,000 * 0.01 = $4,000 * 1.0 (buyer) = $4,000
        # Total buyer: $6,000
        self.assertEqual(result.total_transfer_taxes, Decimal('6000.00'))

    def test_recording_fees_calculation(self):
        """Test deed and mortgage recording fees"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('320000'),
            loan_type='conventional',
        )

        # Deed: $50 + (3 pages * $5) = $65
        # Mortgage: $80 + (10 pages * $5) = $130
        # Surcharge: $20
        # Total: $215
        self.assertEqual(result.total_recording_fees, Decimal('215.00'))

    def test_recordation_tax_tiered(self):
        """Test tiered recordation tax calculation"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('600000'),  # Crosses tier boundary
            loan_type='conventional',
        )

        # Tier 1: $500,000 / $500 = 1,000 increments * $2.50 = $2,500
        # Tier 2: $100,000 / $500 = 200 increments * $5.00 = $1,000
        # School: $600,000 / $500 = 1,200 increments * $0.50 = $600
        # Total: $4,100
        self.assertEqual(result.total_recordation_taxes, Decimal('4100.00'))

    def test_title_fees_calculation(self):
        """Test title search and insurance fees"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('320000'),
            loan_type='conventional',
        )

        # Title search: $250
        # Lender's insurance: $320,000 / $1000 * $5 = $1,600
        # Owner's insurance: $400,000 / $1000 * $5 * 0.9 (discount) = $1,800
        # Total: $3,650
        self.assertEqual(result.total_title_fees, Decimal('3650.00'))

    def test_fha_ufmip_calculation(self):
        """Test FHA UFMIP (Upfront Mortgage Insurance Premium)"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('380000'),
            loan_type='fha',
            down_payment_pct=Decimal('5'),
        )

        # UFMIP: $380,000 * 1.75% = $6,650
        self.assertEqual(result.total_mortgage_insurance, Decimal('6650.00'))

        # Verify UFMIP line item
        ufmip_items = [
            item for item in result.mortgage_insurance
            if item.subcategory == 'ufmip'
        ]
        self.assertEqual(len(ufmip_items), 1)
        self.assertEqual(ufmip_items[0].amount, Decimal('6650.00'))
        self.assertEqual(ufmip_items[0].source, SOURCE_SYSTEM)

    def test_va_funding_fee_first_use(self):
        """Test VA funding fee for first use"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('400000'),
            loan_type='va',
            down_payment_pct=Decimal('0'),
            disabled_veteran=False,
            first_va_use=True,
        )

        # VA funding fee (first use, 0% down): $400,000 * 2.3% = $9,200
        self.assertEqual(result.total_mortgage_insurance, Decimal('9200.00'))

    def test_va_funding_fee_disabled_veteran_waived(self):
        """Test VA funding fee waived for disabled veteran"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('400000'),
            loan_type='va',
            down_payment_pct=Decimal('0'),
            disabled_veteran=True,
            first_va_use=True,
        )

        # VA funding fee waived for disabled veteran
        self.assertEqual(result.total_mortgage_insurance, Decimal('0.00'))

    def test_prepaids_calculation(self):
        """Test prepaid insurance and property tax"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('320000'),
            loan_type='conventional',
            closing_date=date(2025, 6, 15),
        )

        # Homeowners insurance: $400,000 / $1000 * $6.50 = $2,600
        # Property tax proration: $400,000 * 1.0% = $4,000/365 * 165 days = ~$1,808
        # Total prepaids should be around $4,408
        self.assertGreater(result.total_prepaids, Decimal('4000'))
        self.assertLess(result.total_prepaids, Decimal('5000'))

    def test_escrows_calculation(self):
        """Test RESPA-compliant escrow deposits"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('320000'),
            loan_type='conventional',
            closing_date=date(2025, 6, 15),
        )

        # Homeowners insurance escrow: $2,600 / 12 * 2 = ~$433
        # Property tax escrow: $4,000 / 12 * 3 = $1,000
        # Total escrows should be around $1,433
        self.assertGreater(result.total_escrows, Decimal('1400'))
        self.assertLess(result.total_escrows, Decimal('1500'))

    def test_source_tracking_system(self):
        """Test that system-calculated fees have proper source"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('320000'),
            loan_type='conventional',
        )

        # All transfer taxes should have SOURCE_SYSTEM (since sources exist)
        for item in result.transfer_taxes:
            if item.subcategory != 'exemption':
                self.assertEqual(item.source, SOURCE_SYSTEM)

    def test_calculation_trace_present(self):
        """Test that all fees have calculation traces"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('320000'),
            loan_type='conventional',
        )

        # Check that at least one fee has a calculation trace
        all_fees = (
            result.transfer_taxes +
            result.recording_fees +
            result.recordation_taxes +
            result.title_fees +
            result.prepaids +
            result.escrows
        )

        for fee in all_fees:
            self.assertIsInstance(fee.calculation_trace, dict)
            self.assertGreater(len(fee.calculation_trace), 0)

    def test_total_fees_calculation(self):
        """Test that total fees equals sum of all categories"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('320000'),
            loan_type='conventional',
            closing_date=date(2025, 6, 15),
        )

        expected_total = (
            result.total_transfer_taxes +
            result.total_recording_fees +
            result.total_recordation_taxes +
            result.total_title_fees +
            result.total_prepaids +
            result.total_escrows +
            result.total_mortgage_insurance
        )

        self.assertEqual(result.total_fees, expected_total)

    def test_jurisdiction_tracking(self):
        """Test that jurisdiction is properly tracked"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('320000'),
            loan_type='conventional',
        )

        self.assertEqual(result.jurisdiction, "MD-Montgomery")

    def test_fee_line_item_to_dict(self):
        """Test FeeLineItem serialization"""
        item = FeeLineItem(
            category="transfer_tax",
            subcategory="state",
            description="State Transfer Tax",
            amount=Decimal('1000.00'),
            source=SOURCE_SYSTEM,
            source_detail="TaxData v2.0",
            calculation_trace={'rate': 0.005, 'property_value': 400000}
        )

        item_dict = item.to_dict()

        self.assertEqual(item_dict['category'], 'transfer_tax')
        self.assertEqual(item_dict['amount'], 1000.00)
        self.assertIsInstance(item_dict['amount'], float)
        self.assertEqual(item_dict['calculation_trace']['rate'], 0.005)

    def test_fee_calculation_result_to_dict(self):
        """Test FeeCalculationResult serialization"""
        engine = FeeEngine(self.tax_data, "2.0")

        result = engine.calculate_all_fees(
            property_value=Decimal('400000'),
            loan_amount=Decimal('320000'),
            loan_type='conventional',
        )

        result_dict = result.to_dict()

        # Verify structure
        self.assertIn('transfer_taxes', result_dict)
        self.assertIn('total_transfer_taxes', result_dict)
        self.assertIn('deterministic_hash', result_dict)
        self.assertIn('jurisdiction', result_dict)

        # Verify all amounts are floats
        self.assertIsInstance(result_dict['total_fees'], float)
        self.assertIsInstance(result_dict['total_transfer_taxes'], float)


if __name__ == '__main__':
    unittest.main()
