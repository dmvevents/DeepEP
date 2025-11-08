"""
Comprehensive unit tests for API models and views
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import timedelta
from decimal import Decimal

from .models import (
    State, County, TaxData, Municipality,
    ScraperLog, UserProfile, LoanEstimate
)


class StateModelTests(TestCase):
    """Tests for State model"""

    def setUp(self):
        self.state = State.objects.create(
            code='MD',
            name='Maryland',
            active=True
        )

    def test_state_creation(self):
        """Test state can be created"""
        self.assertEqual(self.state.code, 'MD')
        self.assertEqual(self.state.name, 'Maryland')
        self.assertTrue(self.state.active)

    def test_state_str(self):
        """Test string representation"""
        self.assertEqual(str(self.state), 'Maryland (MD)')

    def test_state_unique_code(self):
        """Test state code must be unique"""
        with self.assertRaises(Exception):
            State.objects.create(code='MD', name='Maryland Duplicate')


class CountyModelTests(TestCase):
    """Tests for County model"""

    def setUp(self):
        self.state = State.objects.create(code='MD', name='Maryland')
        self.county = County.objects.create(
            state=self.state,
            name='Montgomery',
            fips_code='24031',
            active=True
        )

    def test_county_creation(self):
        """Test county can be created"""
        self.assertEqual(self.county.name, 'Montgomery')
        self.assertEqual(self.county.state, self.state)
        self.assertEqual(self.county.fips_code, '24031')

    def test_county_str(self):
        """Test string representation"""
        self.assertEqual(str(self.county), 'Montgomery, MD')

    def test_county_unique_per_state(self):
        """Test county name must be unique per state"""
        with self.assertRaises(Exception):
            County.objects.create(
                state=self.state,
                name='Montgomery'
            )


class TaxDataModelTests(TestCase):
    """Tests for TaxData model"""

    def setUp(self):
        self.state = State.objects.create(code='MD', name='Maryland')
        self.county = County.objects.create(state=self.state, name='Montgomery')

        self.tax_data = TaxData.objects.create(
            state=self.state,
            county=self.county,
            version=1,
            is_current=True,
            data_completeness=95,
            scraper_confidence=90,
            data={'property_tax': {'total_rate': 0.01123}},
            effective_date=timezone.now().date(),
            sources=['https://example.gov']
        )

    def test_tax_data_creation(self):
        """Test tax data can be created"""
        self.assertEqual(self.tax_data.version, 1)
        self.assertTrue(self.tax_data.is_current)
        self.assertEqual(self.tax_data.data_completeness, 95)

    def test_tax_data_is_stale(self):
        """Test is_stale property"""
        # Fresh data
        self.assertFalse(self.tax_data.is_stale)

        # Make it stale
        old_date = timezone.now() - timedelta(days=35)
        self.tax_data.last_verified = old_date
        self.tax_data.save()
        self.assertTrue(self.tax_data.is_stale)

    def test_only_one_current_version(self):
        """Test only one version can be current"""
        # Create new version
        new_tax_data = TaxData.objects.create(
            state=self.state,
            county=self.county,
            version=2,
            is_current=True,
            data_completeness=96,
            scraper_confidence=91,
            data={'property_tax': {'total_rate': 0.01124}},
            effective_date=timezone.now().date(),
            sources=['https://example.gov']
        )

        # Original should no longer be current
        self.tax_data.refresh_from_db()
        self.assertFalse(self.tax_data.is_current)
        self.assertTrue(new_tax_data.is_current)


class LoanEstimateModelTests(TestCase):
    """Tests for LoanEstimate model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.state = State.objects.create(code='MD', name='Maryland')
        self.county = County.objects.create(state=self.state, name='Montgomery')
        self.tax_data = TaxData.objects.create(
            state=self.state,
            county=self.county,
            version=1,
            is_current=True,
            data_completeness=95,
            scraper_confidence=90,
            data={},
            effective_date=timezone.now().date()
        )

        self.loan_estimate = LoanEstimate.objects.create(
            user=self.user,
            county=self.county,
            property_value=Decimal('500000'),
            property_type='single_family',
            loan_amount=Decimal('400000'),
            down_payment=Decimal('100000'),
            interest_rate=Decimal('6.5'),
            loan_term_years=30,
            loan_type='conventional',
            first_time_homebuyer=False,
            closing_date=timezone.now().date(),
            calculation_results={'summary': {'monthly_payment': 2528.27}},
            tax_data=self.tax_data,
            is_saved=True,
            name='Test Estimate'
        )

    def test_loan_estimate_creation(self):
        """Test loan estimate can be created"""
        self.assertEqual(self.loan_estimate.user, self.user)
        self.assertEqual(self.loan_estimate.property_value, 500000)
        self.assertTrue(self.loan_estimate.is_saved)

    def test_loan_to_value_calculation(self):
        """Test LTV ratio property"""
        ltv = self.loan_estimate.loan_to_value
        self.assertAlmostEqual(ltv, 80.0, places=2)

    def test_monthly_payment_property(self):
        """Test monthly payment extraction"""
        payment = self.loan_estimate.monthly_payment
        self.assertEqual(payment, 2528.27)


class APIAuthenticationTests(APITestCase):
    """Tests for API authentication"""

    def test_user_registration(self):
        """Test user can register"""
        url = '/api/auth/register/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'first_name': 'New',
            'last_name': 'User'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])

    def test_user_login(self):
        """Test user can login"""
        # Create user
        User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        url = '/api/auth/token/'
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)


class StateAPITests(APITestCase):
    """Tests for State API endpoints"""

    def setUp(self):
        self.state1 = State.objects.create(code='MD', name='Maryland')
        self.state2 = State.objects.create(code='VA', name='Virginia')
        County.objects.create(state=self.state1, name='Montgomery')
        County.objects.create(state=self.state1, name='Howard')

    def test_list_states(self):
        """Test listing all states"""
        url = '/api/states/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_state_counties(self):
        """Test getting counties for a state"""
        url = f'/api/states/{self.state1.id}/counties/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class CountyAPITests(APITestCase):
    """Tests for County API endpoints"""

    def setUp(self):
        self.state = State.objects.create(code='MD', name='Maryland')
        self.county = County.objects.create(
            state=self.state,
            name='Montgomery',
            active=True
        )

    def test_list_counties(self):
        """Test listing counties"""
        url = '/api/counties/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_filter_counties_by_state(self):
        """Test filtering counties by state"""
        url = f'/api/counties/?state={self.state.id}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for county in response.data['results']:
            self.assertEqual(county['state'], self.state.id)


class TaxDataAPITests(APITestCase):
    """Tests for TaxData API endpoints"""

    def setUp(self):
        self.state = State.objects.create(code='MD', name='Maryland')
        self.county = County.objects.create(state=self.state, name='Montgomery')
        self.tax_data = TaxData.objects.create(
            state=self.state,
            county=self.county,
            version=1,
            is_current=True,
            data_completeness=95,
            scraper_confidence=90,
            data={'property_tax': {'total_rate': 0.01}},
            effective_date=timezone.now().date(),
            sources=['https://example.gov']
        )

    def test_get_tax_data_by_location(self):
        """Test getting tax data by state and county"""
        url = '/api/tax-data/by-location/MD/Montgomery/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['state_code'], 'MD')
        self.assertEqual(response.data['county_name'], 'Montgomery')

    def test_get_tax_data_not_found(self):
        """Test getting tax data for non-existent location"""
        url = '/api/tax-data/by-location/XX/Fake/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CalculatorAPITests(APITestCase):
    """Tests for Calculator API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.state = State.objects.create(code='MD', name='Maryland')
        self.county = County.objects.create(state=self.state, name='Montgomery')
        self.tax_data = TaxData.objects.create(
            state=self.state,
            county=self.county,
            version=1,
            is_current=True,
            data_completeness=95,
            scraper_confidence=90,
            data={
                'property_tax': {
                    'total_rate': 0.01,
                    'assessment_ratio': 100
                },
                'transfer_tax': {
                    'state_rate': 0.005,
                    'county_rate': 0.01,
                    'buyer_seller_split': 'seller pays'
                },
                'recordation_tax': {
                    'tiers': [{'max_value': 1000000, 'rate': 0.0035}]
                },
                'recording_fees': {
                    'deed': {'flat': 50, 'per_page': 5},
                    'mortgage': {'flat': 80, 'per_page': 5},
                    'surcharge': 20
                },
                'insurance_estimate': {
                    'base_premium_per_100k': 650
                }
            },
            effective_date=timezone.now().date()
        )

    def test_calculate_loan_estimate(self):
        """Test calculating a loan estimate"""
        url = '/api/calculate/'
        data = {
            'county_id': self.county.id,
            'property_value': 500000,
            'loan_amount': 400000,
            'down_payment': 100000,
            'interest_rate': 6.5,
            'loan_term_years': 30,
            'loan_type': 'conventional',
            'property_type': 'single_family',
            'first_time_homebuyer': False,
            'closing_date': '2025-06-15',
            'save_estimate': False
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('calculation', response.data)
        self.assertIn('section_a', response.data['calculation'])
        self.assertIn('section_b', response.data['calculation'])
        self.assertIn('summary', response.data['calculation'])

    def test_calculate_requires_authentication(self):
        """Test calculation requires authentication"""
        self.client.logout()

        url = '/api/calculate/'
        data = {'county_id': self.county.id}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_calculate_with_invalid_data(self):
        """Test calculation with invalid input"""
        url = '/api/calculate/'
        data = {
            'county_id': self.county.id,
            'property_value': 500000,
            'loan_amount': 600000,  # Exceeds property value
            'down_payment': 0,
            'interest_rate': 6.5,
            'loan_term_years': 30,
            'loan_type': 'conventional',
            'property_type': 'single_family',
            'first_time_homebuyer': False,
            'closing_date': '2025-06-15'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ScraperLogModelTests(TestCase):
    """Tests for ScraperLog model"""

    def setUp(self):
        self.state = State.objects.create(code='MD', name='Maryland')
        self.county = County.objects.create(state=self.state, name='Montgomery')

    def test_scraper_log_creation(self):
        """Test scraper log can be created"""
        log = ScraperLog.objects.create(
            state=self.state,
            county=self.county,
            status='success',
            processing_time=45.5,
            data_completeness=95,
            confidence_score=90,
            sources_found=5,
            llm_provider='anthropic',
            llm_model='claude-3-5-sonnet-20241022',
            trigger_type='manual'
        )

        self.assertEqual(log.status, 'success')
        self.assertEqual(log.processing_time, 45.5)
        self.assertEqual(log.data_completeness, 95)
