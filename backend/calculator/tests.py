"""
Comprehensive unit tests for mortgage calculator engine
"""
from django.test import TestCase
from decimal import Decimal
from datetime import datetime
from calculator.engine import MortgageCalculator


class MortgageCalculatorTests(TestCase):
    """Test suite for MortgageCalculator"""

    def setUp(self):
        """Set up test data"""
        self.sample_tax_data = {
            "state": "MD",
            "county": "Montgomery",
            "property_tax": {
                "total_rate": 0.01123,
                "assessment_ratio": 100,
                "components": {
                    "county": 0.007,
                    "state": 0.001,
                    "municipality": 0.001,
                    "school": 0.0023
                },
                "billing_schedule": {
                    "first_half_due": "September 30",
                    "second_half_due": "December 31"
                },
                "municipalities": []
            },
            "transfer_tax": {
                "state_rate": 0.005,
                "county_rate": 0.01,
                "first_time_buyer_threshold": 500000,
                "first_time_buyer_exemption": "state portion waived",
                "buyer_seller_split": "seller pays"
            },
            "recordation_tax": {
                "tiers": [
                    {"max_value": 500000, "rate": 0.0035},
                    {"min_value": 500000, "rate": 0.005}
                ]
            },
            "recording_fees": {
                "deed": {"flat": 50, "per_page": 5},
                "mortgage": {"flat": 80, "per_page": 5},
                "surcharge": 20
            },
            "insurance_estimate": {
                "base_premium_per_100k": 650
            },
            "sources": []
        }

        self.calculator = MortgageCalculator(self.sample_tax_data)

    def test_monthly_payment_calculation(self):
        """Test monthly payment calculation with standard values"""
        result = self.calculator._calculate_monthly_payment(
            principal=Decimal('400000'),
            annual_rate=Decimal('6.5'),
            years=30
        )

        # Expected: approximately $2,528.27
        self.assertAlmostEqual(float(result), 2528.27, places=1)

    def test_monthly_payment_zero_interest(self):
        """Test monthly payment with 0% interest"""
        result = self.calculator._calculate_monthly_payment(
            principal=Decimal('360000'),
            annual_rate=Decimal('0'),
            years=30
        )

        # Should be principal / months
        expected = 360000 / 360
        self.assertEqual(float(result), expected)

    def test_mortgage_insurance_ltv_under_80(self):
        """Test that no PMI is required when LTV <= 80%"""
        result = self.calculator._calculate_mortgage_insurance(
            loan_amount=Decimal('400000'),
            property_value=Decimal('500000'),
            loan_type='conventional'
        )

        self.assertEqual(float(result), 0)

    def test_mortgage_insurance_ltv_over_80(self):
        """Test PMI is calculated when LTV > 80%"""
        result = self.calculator._calculate_mortgage_insurance(
            loan_amount=Decimal('450000'),
            property_value=Decimal('500000'),
            loan_type='conventional'
        )

        # LTV is 90%, should have PMI
        self.assertGreater(float(result), 0)

    def test_mortgage_insurance_fha(self):
        """Test FHA MIP calculation"""
        result = self.calculator._calculate_mortgage_insurance(
            loan_amount=Decimal('400000'),
            property_value=Decimal('500000'),
            loan_type='fha'
        )

        # FHA has MIP even with good LTV
        self.assertGreater(float(result), 0)

    def test_annual_property_tax(self):
        """Test property tax calculation"""
        result = self.calculator._get_annual_property_tax(
            property_value=Decimal('500000')
        )

        # With 1.123% rate, should be $5,615
        expected = 500000 * 0.01123
        self.assertAlmostEqual(float(result), expected, places=2)

    def test_recording_fees(self):
        """Test recording fees calculation"""
        result = self.calculator._calculate_recording_fees()

        # Deed: 50 + (3 * 5) = 65
        # Mortgage: 80 + (10 * 5) = 130
        # Surcharge: 20
        # Total: 215
        self.assertAlmostEqual(float(result), 215, places=2)

    def test_transfer_taxes_regular_buyer(self):
        """Test transfer tax for regular buyer"""
        result = self.calculator._calculate_transfer_taxes(
            property_value=Decimal('500000'),
            first_time_homebuyer=False
        )

        # Buyer pays 0% (seller pays in this jurisdiction)
        self.assertEqual(float(result), 0)

    def test_transfer_taxes_first_time_buyer(self):
        """Test transfer tax exemption for first-time buyer"""
        result = self.calculator._calculate_transfer_taxes(
            property_value=Decimal('400000'),
            first_time_homebuyer=True
        )

        # Should get state exemption
        self.assertEqual(float(result), 0)

    def test_recordation_tax_single_tier(self):
        """Test recordation tax in first tier"""
        result = self.calculator._calculate_recordation_taxes(
            property_value=Decimal('400000')
        )

        # 400k * 0.0035 = 1400
        expected = 400000 * 0.0035
        self.assertAlmostEqual(float(result), expected, places=2)

    def test_recordation_tax_multiple_tiers(self):
        """Test recordation tax across tiers"""
        result = self.calculator._calculate_recordation_taxes(
            property_value=Decimal('600000')
        )

        # First 500k: 500000 * 0.0035 = 1750
        # Next 100k: 100000 * 0.005 = 500
        # Total: 2250
        expected = (500000 * 0.0035) + (100000 * 0.005)
        self.assertAlmostEqual(float(result), expected, places=2)

    def test_homeowners_insurance(self):
        """Test homeowners insurance estimation"""
        result = self.calculator._get_annual_homeowners_insurance(
            property_value=Decimal('500000')
        )

        # 500k / 100k * 650 = 3250
        expected = 5 * 650
        self.assertAlmostEqual(float(result), expected, places=2)

    def test_section_a_calculation(self):
        """Test Section A: Loan Terms"""
        result = self.calculator._calculate_section_a(
            loan_amount=Decimal('400000'),
            interest_rate=Decimal('6.5'),
            loan_term_years=30
        )

        self.assertEqual(result['loan_amount'], 400000)
        self.assertEqual(result['interest_rate'], 6.5)
        self.assertEqual(result['loan_term_years'], 30)
        self.assertEqual(result['loan_term_months'], 360)
        self.assertGreater(result['monthly_principal_and_interest'], 2000)
        self.assertFalse(result['prepayment_penalty'])

    def test_section_b_calculation(self):
        """Test Section B: Projected Payments"""
        result = self.calculator._calculate_section_b(
            loan_amount=Decimal('400000'),
            interest_rate=Decimal('6.5'),
            loan_term_years=30,
            property_value=Decimal('500000'),
            loan_type='conventional',
            closing_date=datetime(2025, 6, 15)
        )

        self.assertIn('monthly_principal_and_interest', result)
        self.assertIn('mortgage_insurance', result)
        self.assertIn('estimated_escrow', result)
        self.assertIn('estimated_total_monthly_payment', result)
        self.assertAlmostEqual(result['ltv_ratio'], 80, places=2)

    def test_section_e_calculation(self):
        """Test Section E: Taxes and Government Fees"""
        result = self.calculator._calculate_section_e(
            property_value=Decimal('500000'),
            first_time_homebuyer=False
        )

        self.assertIn('recording_fees', result)
        self.assertIn('transfer_taxes', result)
        self.assertIn('recordation_taxes', result)
        self.assertIn('total_taxes_and_fees', result)
        self.assertGreater(result['total_taxes_and_fees'], 0)

    def test_full_calculation(self):
        """Test complete loan estimate calculation"""
        result = self.calculator.calculate(
            property_value=Decimal('500000'),
            loan_amount=Decimal('400000'),
            down_payment=Decimal('100000'),
            interest_rate=Decimal('6.5'),
            loan_term_years=30,
            closing_date=datetime(2025, 6, 15),
            loan_type='conventional',
            property_type='single_family',
            first_time_homebuyer=False
        )

        # Check all sections exist
        self.assertIn('section_a', result)
        self.assertIn('section_b', result)
        self.assertIn('section_c', result)
        self.assertIn('section_e', result)
        self.assertIn('section_g', result)
        self.assertIn('section_h', result)
        self.assertIn('summary', result)

        # Check summary has required fields
        summary = result['summary']
        self.assertIn('monthly_payment', summary)
        self.assertIn('cash_to_close', summary)
        self.assertIn('total_closing_costs', summary)

    def test_validation_negative_property_value(self):
        """Test validation rejects negative property value"""
        with self.assertRaises(ValueError):
            self.calculator.calculate(
                property_value=Decimal('-500000'),
                loan_amount=Decimal('400000'),
                down_payment=Decimal('100000'),
                interest_rate=Decimal('6.5'),
                loan_term_years=30,
                closing_date=datetime(2025, 6, 15)
            )

    def test_validation_loan_exceeds_property_value(self):
        """Test validation rejects loan > property value"""
        with self.assertRaises(ValueError):
            self.calculator.calculate(
                property_value=Decimal('500000'),
                loan_amount=Decimal('600000'),
                down_payment=Decimal('0'),
                interest_rate=Decimal('6.5'),
                loan_term_years=30,
                closing_date=datetime(2025, 6, 15)
            )

    def test_validation_invalid_interest_rate(self):
        """Test validation rejects invalid interest rate"""
        with self.assertRaises(ValueError):
            self.calculator.calculate(
                property_value=Decimal('500000'),
                loan_amount=Decimal('400000'),
                down_payment=Decimal('100000'),
                interest_rate=Decimal('25'),  # Over 20%
                loan_term_years=30,
                closing_date=datetime(2025, 6, 15)
            )

    def test_calculation_consistency(self):
        """Test that multiple calculations with same inputs give same results"""
        result1 = self.calculator.calculate(
            property_value=Decimal('500000'),
            loan_amount=Decimal('400000'),
            down_payment=Decimal('100000'),
            interest_rate=Decimal('6.5'),
            loan_term_years=30,
            closing_date=datetime(2025, 6, 15)
        )

        result2 = self.calculator.calculate(
            property_value=Decimal('500000'),
            loan_amount=Decimal('400000'),
            down_payment=Decimal('100000'),
            interest_rate=Decimal('6.5'),
            loan_term_years=30,
            closing_date=datetime(2025, 6, 15)
        )

        self.assertEqual(
            result1['summary']['monthly_payment'],
            result2['summary']['monthly_payment']
        )
