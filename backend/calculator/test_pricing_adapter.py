"""
Unit tests for Pricing Adapter - Phase 3: Scenario Desk

Tests the pricing adapter interface, mock implementation, and 3 rails logic.

Author: Backend/Django Engineer
Date: November 10, 2025
"""

import os
import django

# Configure Django settings before importing any Django modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import unittest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch

from calculator.pricing_adapter import (
    LoanParameters,
    PricingOption,
    PricingResponse,
    PricingAdapter,
    MockPricingAdapter,
    PricingService,
    PricingError,
)


class TestLoanParameters(unittest.TestCase):
    """Test LoanParameters dataclass"""

    def test_ltv_calculation(self):
        """Test LTV ratio calculation"""
        params = LoanParameters(
            loan_amount=Decimal('400000'),
            property_value=Decimal('500000'),
            credit_score=720,
            loan_type='conventional',
            occupancy='primary',
            property_type='single_family',
            loan_term_months=360,
            loan_purpose='purchase',
            documentation_type='full_doc',
        )
        self.assertEqual(params.ltv_ratio, Decimal('80.00'))

    def test_ltv_zero_property_value(self):
        """Test LTV calculation with zero property value"""
        params = LoanParameters(
            loan_amount=Decimal('400000'),
            property_value=Decimal('0'),
            credit_score=720,
            loan_type='conventional',
            occupancy='primary',
            property_type='single_family',
            loan_term_months=360,
            loan_purpose='purchase',
            documentation_type='full_doc',
        )
        self.assertEqual(params.ltv_ratio, Decimal('0'))


class TestPricingOption(unittest.TestCase):
    """Test PricingOption dataclass"""

    def test_effective_rate_calculation(self):
        """Test effective rate calculation with points"""
        option = PricingOption(
            rate=Decimal('6.750'),
            points=Decimal('1.000'),
            credit=Decimal('0'),
        )
        # 1% points reduces rate by ~0.25%
        expected = Decimal('6.500')
        self.assertEqual(option.effective_rate, expected)

    def test_net_cost_calculation(self):
        """Test net cost calculation"""
        option = PricingOption(
            rate=Decimal('6.750'),
            points=Decimal('2.000'),
            credit=Decimal('500'),
        )
        # 2% points - $500 credit = -498 (since credit is in dollars, not percent)
        # The borrower pays 2% points minus $500 credit
        self.assertEqual(option.net_cost, Decimal('-498.000'))

    def test_upfront_cost_calculation(self):
        """Test upfront cost in dollars"""
        option = PricingOption(
            rate=Decimal('6.750'),
            points=Decimal('1.000'),
            credit=Decimal('2000'),
        )
        loan_amount = Decimal('400000')
        # 1% of 400k = 4000, minus 2000 credit = 2000
        expected = Decimal('2000.00')
        self.assertEqual(option.get_upfront_cost(loan_amount), expected)

    def test_upfront_cost_with_credit(self):
        """Test upfront cost with lender credit (negative cost)"""
        option = PricingOption(
            rate=Decimal('7.000'),
            points=Decimal('0.000'),
            credit=Decimal('5000'),
        )
        loan_amount = Decimal('400000')
        # 0 points - 5000 credit = -5000 (borrower receives credit)
        expected = Decimal('-5000.00')
        self.assertEqual(option.get_upfront_cost(loan_amount), expected)


class TestPricingResponse(unittest.TestCase):
    """Test PricingResponse dataclass"""

    def setUp(self):
        """Set up test data"""
        self.loan_params = LoanParameters(
            loan_amount=Decimal('400000'),
            property_value=Decimal('500000'),
            credit_score=720,
            loan_type='conventional',
            occupancy='primary',
            property_type='single_family',
            loan_term_months=360,
            loan_purpose='purchase',
            documentation_type='full_doc',
        )

        self.options = [
            PricingOption(rate=Decimal('6.500'), points=Decimal('2.000'), credit=Decimal('0')),
            PricingOption(rate=Decimal('6.750'), points=Decimal('1.000'), credit=Decimal('0')),
            PricingOption(rate=Decimal('7.000'), points=Decimal('0.000'), credit=Decimal('0')),
            PricingOption(rate=Decimal('7.250'), points=Decimal('0.000'), credit=Decimal('2000')),
        ]

    def test_get_best_rate_option(self):
        """Test finding option with lowest rate"""
        response = PricingResponse(
            options=self.options,
            loan_parameters=self.loan_params,
            timestamp=datetime.now(),
            provider='TestProvider',
        )
        best = response.get_best_rate_option()
        self.assertEqual(best.rate, Decimal('6.500'))

    def test_get_zero_cost_option(self):
        """Test finding option closest to zero cost"""
        response = PricingResponse(
            options=self.options,
            loan_parameters=self.loan_params,
            timestamp=datetime.now(),
            provider='TestProvider',
        )
        zero_cost = response.get_zero_cost_option()
        # Option with 0 points and 0 credit
        self.assertEqual(zero_cost.rate, Decimal('7.000'))

    def test_get_max_credit_option(self):
        """Test finding option with maximum credit"""
        response = PricingResponse(
            options=self.options,
            loan_parameters=self.loan_params,
            timestamp=datetime.now(),
            provider='TestProvider',
        )
        max_credit = response.get_max_credit_option()
        self.assertEqual(max_credit.credit, Decimal('2000'))

    def test_empty_options(self):
        """Test response with no options"""
        response = PricingResponse(
            options=[],
            loan_parameters=self.loan_params,
            timestamp=datetime.now(),
            provider='TestProvider',
        )
        self.assertIsNone(response.get_best_rate_option())
        self.assertIsNone(response.get_zero_cost_option())
        self.assertIsNone(response.get_max_credit_option())


class TestMockPricingAdapter(unittest.TestCase):
    """Test MockPricingAdapter implementation"""

    def setUp(self):
        """Set up adapter and test parameters"""
        self.adapter = MockPricingAdapter()
        self.loan_params = LoanParameters(
            loan_amount=Decimal('400000'),
            property_value=Decimal('500000'),
            credit_score=720,
            loan_type='conventional',
            occupancy='primary',
            property_type='single_family',
            loan_term_months=360,
            loan_purpose='purchase',
            documentation_type='full_doc',
        )

    def test_validate_parameters_valid(self):
        """Test parameter validation with valid input"""
        is_valid, errors = self.adapter.validate_parameters(self.loan_params)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_parameters_invalid_loan_amount(self):
        """Test validation with invalid loan amount"""
        params = LoanParameters(
            loan_amount=Decimal('-100'),
            property_value=Decimal('500000'),
            credit_score=720,
            loan_type='conventional',
            occupancy='primary',
            property_type='single_family',
            loan_term_months=360,
            loan_purpose='purchase',
            documentation_type='full_doc',
        )
        is_valid, errors = self.adapter.validate_parameters(params)
        self.assertFalse(is_valid)
        self.assertIn("Loan amount must be positive", errors)

    def test_validate_parameters_invalid_credit_score(self):
        """Test validation with invalid credit score"""
        params = LoanParameters(
            loan_amount=Decimal('400000'),
            property_value=Decimal('500000'),
            credit_score=900,
            loan_type='conventional',
            occupancy='primary',
            property_type='single_family',
            loan_term_months=360,
            loan_purpose='purchase',
            documentation_type='full_doc',
        )
        is_valid, errors = self.adapter.validate_parameters(params)
        self.assertFalse(is_valid)
        self.assertIn("Credit score must be between 300 and 850", errors)

    def test_validate_parameters_high_ltv(self):
        """Test validation with LTV exceeding maximum"""
        params = LoanParameters(
            loan_amount=Decimal('490000'),
            property_value=Decimal('500000'),
            credit_score=720,
            loan_type='conventional',
            occupancy='primary',
            property_type='single_family',
            loan_term_months=360,
            loan_purpose='purchase',
            documentation_type='full_doc',
        )
        is_valid, errors = self.adapter.validate_parameters(params)
        self.assertFalse(is_valid)
        self.assertTrue(any("LTV ratio exceeds maximum" in err for err in errors))

    def test_get_pricing_success(self):
        """Test successful pricing request"""
        response = self.adapter.get_pricing(self.loan_params)

        self.assertIsNone(response.error)
        self.assertEqual(response.provider, 'MockInvestor')
        self.assertGreater(len(response.options), 0)
        self.assertGreaterEqual(len(response.options), 5)  # Should have 7 options

    def test_get_pricing_generates_multiple_options(self):
        """Test that pricing generates multiple options (3 rails)"""
        response = self.adapter.get_pricing(self.loan_params)

        # Should have 7 options
        self.assertEqual(len(response.options), 7)

        # Verify rates increase as we move from high points to high credit
        rates = [opt.rate for opt in response.options]
        self.assertEqual(rates, sorted(rates))  # Rates should be in ascending order

    def test_get_pricing_credit_score_adjustment(self):
        """Test that lower credit scores result in higher rates"""
        # High credit score
        params_high_credit = LoanParameters(
            loan_amount=Decimal('400000'),
            property_value=Decimal('500000'),
            credit_score=780,
            loan_type='conventional',
            occupancy='primary',
            property_type='single_family',
            loan_term_months=360,
            loan_purpose='purchase',
            documentation_type='full_doc',
        )
        response_high = self.adapter.get_pricing(params_high_credit)

        # Low credit score
        params_low_credit = LoanParameters(
            loan_amount=Decimal('400000'),
            property_value=Decimal('500000'),
            credit_score=640,
            loan_type='conventional',
            occupancy='primary',
            property_type='single_family',
            loan_term_months=360,
            loan_purpose='purchase',
            documentation_type='full_doc',
        )
        response_low = self.adapter.get_pricing(params_low_credit)

        # Low credit should have higher rates
        best_high = response_high.get_best_rate_option()
        best_low = response_low.get_best_rate_option()
        self.assertGreater(best_low.rate, best_high.rate)

    def test_get_pricing_occupancy_adjustment(self):
        """Test that investment properties have higher rates"""
        # Primary residence
        params_primary = LoanParameters(
            loan_amount=Decimal('400000'),
            property_value=Decimal('500000'),
            credit_score=720,
            loan_type='conventional',
            occupancy='primary',
            property_type='single_family',
            loan_term_months=360,
            loan_purpose='purchase',
            documentation_type='full_doc',
        )
        response_primary = self.adapter.get_pricing(params_primary)

        # Investment property
        params_investment = LoanParameters(
            loan_amount=Decimal('400000'),
            property_value=Decimal('500000'),
            credit_score=720,
            loan_type='conventional',
            occupancy='investment',
            property_type='single_family',
            loan_term_months=360,
            loan_purpose='purchase',
            documentation_type='full_doc',
        )
        response_investment = self.adapter.get_pricing(params_investment)

        # Investment should have higher rates
        best_primary = response_primary.get_best_rate_option()
        best_investment = response_investment.get_best_rate_option()
        self.assertGreater(best_investment.rate, best_primary.rate)

    def test_get_pricing_with_validation_error(self):
        """Test pricing request with invalid parameters"""
        params = LoanParameters(
            loan_amount=Decimal('-100'),
            property_value=Decimal('500000'),
            credit_score=720,
            loan_type='conventional',
            occupancy='primary',
            property_type='single_family',
            loan_term_months=360,
            loan_purpose='purchase',
            documentation_type='full_doc',
        )
        response = self.adapter.get_pricing(params)

        self.assertIsNotNone(response.error)
        self.assertEqual(len(response.options), 0)

    def test_3_rails_logic(self):
        """Test that pricing options demonstrate 3 rails (rate/points/credit)"""
        response = self.adapter.get_pricing(self.loan_params)

        # Find specific option types
        best_rate = response.get_best_rate_option()
        zero_cost = response.get_zero_cost_option()
        max_credit = response.get_max_credit_option()

        # Rail 1: Best rate should have highest points
        self.assertGreater(best_rate.points, Decimal('0'))
        self.assertEqual(best_rate.credit, Decimal('0'))

        # Rail 2: Zero cost should have no points or credit
        self.assertEqual(zero_cost.points, Decimal('0'))
        self.assertEqual(zero_cost.credit, Decimal('0'))

        # Rail 3: Max credit should have highest credit
        self.assertGreater(max_credit.credit, Decimal('0'))
        self.assertGreater(max_credit.rate, best_rate.rate)


class TestPricingService(unittest.TestCase):
    """Test PricingService with multiple adapters"""

    def setUp(self):
        """Set up service with mock adapters"""
        self.primary_adapter = MockPricingAdapter()
        self.fallback_adapter = MockPricingAdapter()
        self.service = PricingService(
            primary_adapter=self.primary_adapter,
            fallback_adapter=self.fallback_adapter,
        )

        self.loan_params = LoanParameters(
            loan_amount=Decimal('400000'),
            property_value=Decimal('500000'),
            credit_score=720,
            loan_type='conventional',
            occupancy='primary',
            property_type='single_family',
            loan_term_months=360,
            loan_purpose='purchase',
            documentation_type='full_doc',
        )

    def test_get_pricing_success(self):
        """Test successful pricing with primary adapter"""
        response = self.service.get_pricing(self.loan_params)

        self.assertIsNone(response.error)
        self.assertGreater(len(response.options), 0)

    def test_get_pricing_fallback_on_error(self):
        """Test fallback to secondary adapter on primary error"""
        # Mock primary adapter to raise error
        with patch.object(self.primary_adapter, 'get_pricing', side_effect=Exception("API Error")):
            response = self.service.get_pricing(self.loan_params)

            # Should succeed with fallback
            self.assertIsNone(response.error)
            self.assertGreater(len(response.options), 0)

    def test_get_pricing_fallback_on_error_response(self):
        """Test fallback when primary returns error response"""
        # Mock primary to return error response
        error_response = PricingResponse(
            options=[],
            loan_parameters=self.loan_params,
            timestamp=datetime.now(),
            provider='Primary',
            error='API unavailable',
        )

        with patch.object(self.primary_adapter, 'get_pricing', return_value=error_response):
            response = self.service.get_pricing(self.loan_params)

            # Should use fallback
            self.assertEqual(response.provider, 'MockInvestor')
            self.assertGreater(len(response.options), 0)

    def test_get_pricing_no_fallback(self):
        """Test error when no fallback adapter available"""
        service_no_fallback = PricingService(primary_adapter=self.primary_adapter)

        with patch.object(self.primary_adapter, 'get_pricing', side_effect=Exception("API Error")):
            with self.assertRaises(PricingError) as context:
                service_no_fallback.get_pricing(self.loan_params)

            self.assertIn("API Error", str(context.exception))

    def test_get_pricing_both_fail(self):
        """Test error when both primary and fallback fail"""
        with patch.object(self.primary_adapter, 'get_pricing', side_effect=Exception("Primary Error")):
            with patch.object(self.fallback_adapter, 'get_pricing', side_effect=Exception("Fallback Error")):
                with self.assertRaises(PricingError) as context:
                    self.service.get_pricing(self.loan_params)

                self.assertIn("Both primary and fallback", str(context.exception))


class TestPricingError(unittest.TestCase):
    """Test PricingError exception"""

    def test_error_with_code(self):
        """Test error with error code"""
        error = PricingError("Test error", code="TEST_CODE")
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.code, "TEST_CODE")

    def test_error_with_details(self):
        """Test error with additional details"""
        details = {'field': 'credit_score', 'value': 900}
        error = PricingError("Invalid credit score", code="VALIDATION_ERROR", details=details)
        self.assertEqual(error.details, details)


if __name__ == '__main__':
    unittest.main()
