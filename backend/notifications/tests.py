"""
Unit tests for notification service
"""
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from unittest.mock import patch, MagicMock

from .models import NotificationLog
from .service import NotificationService
from .providers import ConsoleEmailProvider, ConsoleSMSProvider
from .templates.sms.templates import render_sms_message
from api.models import LoanEstimate, County, State, TaxData


class NotificationServiceTestCase(TestCase):
    """Test notification service"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = NotificationService()

    @override_settings(
        NOTIFICATIONS_ENABLED=True,
        ENABLE_EMAIL_NOTIFICATIONS=True,
        EMAIL_PROVIDER='console'
    )
    def test_send_email_notification(self):
        """Test sending email notification"""
        context = {
            'borrower_name': 'Test User',
            'application_id': 123,
            'property_address': '123 Test St',
            'loan_amount': '500,000',
            'submitted_date': 'January 1, 2025',
            'application_url': 'http://test.com/app/123',
        }

        notification_log = self.service.send_email_notification(
            user=self.user,
            milestone='application_submitted',
            context=context,
        )

        # Verify log created
        self.assertIsNotNone(notification_log)
        self.assertEqual(notification_log.user, self.user)
        self.assertEqual(notification_log.notification_type, 'email')
        self.assertEqual(notification_log.milestone, 'application_submitted')
        self.assertEqual(notification_log.status, 'sent')
        self.assertEqual(notification_log.recipient_email, 'test@example.com')

    @override_settings(NOTIFICATIONS_ENABLED=False)
    def test_email_disabled(self):
        """Test email when notifications disabled"""
        notification_log = self.service.send_email_notification(
            user=self.user,
            milestone='welcome',
            context={},
        )

        self.assertEqual(notification_log.status, 'failed')
        self.assertIn('disabled', notification_log.error_message)

    @override_settings(
        NOTIFICATIONS_ENABLED=True,
        ENABLE_SMS_NOTIFICATIONS=True,
        SMS_PROVIDER='console'
    )
    def test_send_sms_notification(self):
        """Test sending SMS notification"""
        context = {
            'application_id': 123,
            'short_url': 'http://short.url/123',
        }

        # Mock phone number
        with patch.object(self.service, '_get_user_phone', return_value='+15551234567'):
            notification_log = self.service.send_sms_notification(
                user=self.user,
                milestone='application_submitted',
                context=context,
            )

        # Verify log created
        self.assertEqual(notification_log.notification_type, 'sms')
        self.assertEqual(notification_log.status, 'sent')
        self.assertEqual(notification_log.recipient_phone, '+15551234567')

    @override_settings(
        NOTIFICATIONS_ENABLED=True,
        NOTIFICATION_RATE_LIMIT_PER_USER=2,
        NOTIFICATION_RATE_LIMIT_WINDOW=3600
    )
    def test_rate_limiting(self):
        """Test rate limiting"""
        # Create 2 recent notifications (at the limit)
        for i in range(2):
            NotificationLog.objects.create(
                user=self.user,
                notification_type='email',
                milestone='test',
                status='sent',
                created_at=timezone.now(),
            )

        # Third notification should be rate limited
        is_limited = self.service._is_rate_limited(self.user)
        self.assertTrue(is_limited)

    def test_email_subject_generation(self):
        """Test email subject generation"""
        subject = self.service._get_email_subject('application_approved', {})
        self.assertEqual(subject, 'Congratulations! Application Approved')

        subject = self.service._get_email_subject('welcome', {})
        self.assertEqual(subject, 'Welcome to Mortgage Calculator')


class SMSTemplateTestCase(TestCase):
    """Test SMS template rendering"""

    def test_render_sms_application_submitted(self):
        """Test application_submitted SMS template"""
        context = {
            'application_id': 123,
            'short_url': 'http://test.com/123',
        }
        message = render_sms_message('application_submitted', context)

        self.assertIn('123', message)
        self.assertIn('http://test.com/123', message)
        self.assertIn('STOP', message)  # Opt-out language

    def test_render_sms_application_approved(self):
        """Test application_approved SMS template"""
        context = {
            'loan_amount': '500,000',
            'short_url': 'http://test.com/123',
        }
        message = render_sms_message('application_approved', context)

        self.assertIn('CONGRATULATIONS', message.upper())
        self.assertIn('500,000', message)
        self.assertIn('STOP', message)

    def test_render_sms_missing_context(self):
        """Test SMS rendering with missing context"""
        with self.assertRaises(ValueError):
            render_sms_message('application_submitted', {})  # Missing required fields


class EmailProviderTestCase(TestCase):
    """Test email providers"""

    def test_console_email_provider(self):
        """Test console email provider"""
        provider = ConsoleEmailProvider()

        result = provider.send_email(
            to_email='test@example.com',
            subject='Test Subject',
            html_content='<p>Test HTML</p>',
            text_content='Test text',
        )

        self.assertTrue(result['success'])
        self.assertIn('console', result['message_id'])
        self.assertEqual(result['error'], '')


class SMSProviderTestCase(TestCase):
    """Test SMS providers"""

    def test_console_sms_provider(self):
        """Test console SMS provider"""
        provider = ConsoleSMSProvider()

        result = provider.send_sms(
            to_phone='+15551234567',
            message='Test message',
        )

        self.assertTrue(result['success'])
        self.assertIn('console-sms', result['message_id'])
        self.assertEqual(result['error'], '')


class NotificationSignalsTestCase(TestCase):
    """Test notification signals"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create state and county
        self.state = State.objects.create(code='MD', name='Maryland')
        self.county = County.objects.create(state=self.state, name='Montgomery')

        # Create tax data
        self.tax_data = TaxData.objects.create(
            state=self.state,
            county=self.county,
            version=1,
            data_completeness=100,
            scraper_confidence=95,
            data={},
            effective_date=timezone.now().date(),
        )

    @override_settings(NOTIFICATIONS_ENABLED=True, ENABLE_EMAIL_NOTIFICATIONS=True)
    @patch('notifications.tasks.send_email_notification_task.delay')
    def test_loan_estimate_submitted_signal(self, mock_task):
        """Test notification sent when loan estimate submitted"""
        loan_estimate = LoanEstimate.objects.create(
            user=self.user,
            county=self.county,
            property_value=500000,
            loan_amount=400000,
            down_payment=100000,
            interest_rate=6.5,
            loan_type='conventional',
            property_type='single_family',
            closing_date=timezone.now().date(),
            calculation_results={},
            tax_data=self.tax_data,
            status='submitted',  # Trigger notification
            submitted_at=timezone.now(),
        )

        # Verify task was called
        mock_task.assert_called_once()
        call_args = mock_task.call_args[1]
        self.assertEqual(call_args['user_id'], self.user.id)
        self.assertEqual(call_args['milestone'], 'application_submitted')

    @override_settings(NOTIFICATIONS_ENABLED=True, ENABLE_EMAIL_NOTIFICATIONS=True)
    @patch('notifications.tasks.send_email_notification_task.delay')
    def test_loan_estimate_approved_signal(self, mock_task):
        """Test notification sent when loan estimate approved"""
        loan_estimate = LoanEstimate.objects.create(
            user=self.user,
            county=self.county,
            property_value=500000,
            loan_amount=400000,
            down_payment=100000,
            interest_rate=6.5,
            loan_type='conventional',
            property_type='single_family',
            closing_date=timezone.now().date(),
            calculation_results={},
            tax_data=self.tax_data,
            status='submitted',
        )

        mock_task.reset_mock()

        # Update to approved
        loan_estimate.status = 'approved'
        loan_estimate.reviewed_at = timezone.now()
        loan_estimate.save()

        # Verify task was called
        mock_task.assert_called_once()
        call_args = mock_task.call_args[1]
        self.assertEqual(call_args['milestone'], 'application_approved')

    @override_settings(NOTIFICATIONS_ENABLED=True, ENABLE_EMAIL_NOTIFICATIONS=True)
    @patch('notifications.tasks.send_email_notification_task.delay')
    def test_welcome_notification_on_user_creation(self, mock_task):
        """Test welcome notification sent when user created"""
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='testpass123'
        )

        # Verify task was called
        mock_task.assert_called_once()
        call_args = mock_task.call_args[1]
        self.assertEqual(call_args['user_id'], new_user.id)
        self.assertEqual(call_args['milestone'], 'welcome')


class NotificationLogModelTestCase(TestCase):
    """Test NotificationLog model"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_notification_log(self):
        """Test creating notification log"""
        log = NotificationLog.objects.create(
            user=self.user,
            notification_type='email',
            milestone='application_submitted',
            status='sent',
            recipient_email='test@example.com',
            subject='Test Subject',
            message_preview='Test message preview',
            provider='console',
            sent_at=timezone.now(),
        )

        self.assertEqual(log.user, self.user)
        self.assertEqual(log.notification_type, 'email')
        self.assertEqual(log.status, 'sent')

    def test_notification_log_string_representation(self):
        """Test __str__ method"""
        log = NotificationLog.objects.create(
            user=self.user,
            notification_type='email',
            milestone='application_submitted',
            status='sent',
            recipient_email='test@example.com',
            subject='Test',
            message_preview='Preview',
            provider='console',
        )

        str_repr = str(log)
        self.assertIn('Application Submitted', str_repr)
        self.assertIn('test@example.com', str_repr)
