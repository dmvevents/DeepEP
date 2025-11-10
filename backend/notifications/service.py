"""
Notification service layer.
High-level API for sending notifications with template rendering and logging.
"""
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

from .providers import get_email_provider, get_sms_provider
from .templates.sms.templates import render_sms_message
from .models import NotificationLog

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Notification service for sending emails and SMS.
    Handles template rendering, provider abstraction, and audit logging.
    """

    def __init__(self):
        self.email_provider = get_email_provider()
        self.sms_provider = get_sms_provider()

    def send_email_notification(
        self,
        user: User,
        milestone: str,
        context: Dict[str, Any],
        template_name: Optional[str] = None,
    ) -> NotificationLog:
        """
        Send email notification for a milestone.

        Args:
            user: User to notify
            milestone: Milestone key (e.g., 'application_submitted')
            context: Template context variables
            template_name: Optional custom template name

        Returns:
            NotificationLog instance
        """
        # Check if notifications enabled
        if not settings.NOTIFICATIONS_ENABLED or not settings.ENABLE_EMAIL_NOTIFICATIONS:
            logger.info(f"Email notifications disabled, skipping: {milestone}")
            return self._create_log(
                user=user,
                notification_type='email',
                milestone=milestone,
                status='failed',
                error_message='Email notifications disabled in settings'
            )

        # Check rate limit
        if self._is_rate_limited(user):
            logger.warning(f"Rate limit exceeded for user {user.id}")
            return self._create_log(
                user=user,
                notification_type='email',
                milestone=milestone,
                status='failed',
                error_message='Rate limit exceeded'
            )

        # Get recipient email
        recipient_email = user.email
        if not recipient_email:
            logger.warning(f"User {user.id} has no email address")
            return self._create_log(
                user=user,
                notification_type='email',
                milestone=milestone,
                status='failed',
                error_message='User has no email address'
            )

        # Add default context
        context.setdefault('borrower_name', user.get_full_name() or user.username)
        context.setdefault('year', datetime.datetime.now().year)
        context.setdefault('dashboard_url', self._get_dashboard_url())

        # Render template
        template_name = template_name or f'email/{milestone}.html'
        try:
            html_content = render_to_string(template_name, context)
            text_content = strip_tags(html_content)
        except Exception as e:
            logger.error(f"Template rendering failed for {template_name}: {str(e)}")
            return self._create_log(
                user=user,
                notification_type='email',
                milestone=milestone,
                status='failed',
                error_message=f'Template error: {str(e)}'
            )

        # Generate subject
        subject = self._get_email_subject(milestone, context)

        # Create log entry
        notification_log = self._create_log(
            user=user,
            notification_type='email',
            milestone=milestone,
            recipient_email=recipient_email,
            subject=subject,
            message_preview=text_content[:200],
            provider=settings.EMAIL_PROVIDER,
        )

        # Send email
        result = self.email_provider.send_email(
            to_email=recipient_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

        # Update log
        if result['success']:
            notification_log.status = 'sent'
            notification_log.sent_at = timezone.now()
            notification_log.provider_message_id = result['message_id']
            logger.info(f"Email sent to {recipient_email}: {milestone}")
        else:
            notification_log.status = 'failed'
            notification_log.error_message = result['error']
            logger.error(f"Email failed to {recipient_email}: {result['error']}")

        notification_log.save()
        return notification_log

    def send_sms_notification(
        self,
        user: User,
        milestone: str,
        context: Dict[str, Any],
        phone_number: Optional[str] = None,
    ) -> NotificationLog:
        """
        Send SMS notification for a milestone.

        Args:
            user: User to notify
            milestone: Milestone key
            context: Template context variables
            phone_number: Optional phone override (defaults to user profile)

        Returns:
            NotificationLog instance
        """
        # Check if notifications enabled
        if not settings.NOTIFICATIONS_ENABLED or not settings.ENABLE_SMS_NOTIFICATIONS:
            logger.info(f"SMS notifications disabled, skipping: {milestone}")
            return self._create_log(
                user=user,
                notification_type='sms',
                milestone=milestone,
                status='failed',
                error_message='SMS notifications disabled in settings'
            )

        # Check rate limit
        if self._is_rate_limited(user):
            logger.warning(f"Rate limit exceeded for user {user.id}")
            return self._create_log(
                user=user,
                notification_type='sms',
                milestone=milestone,
                status='failed',
                error_message='Rate limit exceeded'
            )

        # Get recipient phone
        recipient_phone = phone_number or self._get_user_phone(user)
        if not recipient_phone:
            logger.warning(f"User {user.id} has no phone number")
            return self._create_log(
                user=user,
                notification_type='sms',
                milestone=milestone,
                status='failed',
                error_message='User has no phone number'
            )

        # Render SMS message
        try:
            message = render_sms_message(milestone, context)
        except Exception as e:
            logger.error(f"SMS template error for {milestone}: {str(e)}")
            return self._create_log(
                user=user,
                notification_type='sms',
                milestone=milestone,
                status='failed',
                error_message=f'Template error: {str(e)}'
            )

        # Create log entry
        notification_log = self._create_log(
            user=user,
            notification_type='sms',
            milestone=milestone,
            recipient_phone=recipient_phone,
            message_preview=message[:200],
            provider=settings.SMS_PROVIDER,
        )

        # Send SMS
        result = self.sms_provider.send_sms(
            to_phone=recipient_phone,
            message=message,
        )

        # Update log
        if result['success']:
            notification_log.status = 'sent'
            notification_log.sent_at = timezone.now()
            notification_log.provider_message_id = result['message_id']
            logger.info(f"SMS sent to {recipient_phone}: {milestone}")
        else:
            notification_log.status = 'failed'
            notification_log.error_message = result['error']
            logger.error(f"SMS failed to {recipient_phone}: {result['error']}")

        notification_log.save()
        return notification_log

    def _create_log(
        self,
        user: User,
        notification_type: str,
        milestone: str,
        status: str = 'pending',
        recipient_email: str = '',
        recipient_phone: str = '',
        subject: str = '',
        message_preview: str = '',
        provider: str = '',
        error_message: str = '',
    ) -> NotificationLog:
        """Create notification log entry"""
        return NotificationLog.objects.create(
            user=user,
            notification_type=notification_type,
            milestone=milestone,
            status=status,
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            subject=subject,
            message_preview=message_preview,
            provider=provider,
            error_message=error_message,
        )

    def _is_rate_limited(self, user: User) -> bool:
        """Check if user has exceeded rate limit"""
        window_start = timezone.now() - timezone.timedelta(
            seconds=settings.NOTIFICATION_RATE_LIMIT_WINDOW
        )

        recent_count = NotificationLog.objects.filter(
            user=user,
            created_at__gte=window_start,
        ).count()

        return recent_count >= settings.NOTIFICATION_RATE_LIMIT_PER_USER

    def _get_email_subject(self, milestone: str, context: Dict[str, Any]) -> str:
        """Generate email subject line"""
        subjects = {
            'application_submitted': 'Application Submitted Successfully',
            'application_under_review': 'Your Application is Under Review',
            'application_needs_correction': 'Action Required: Application Corrections',
            'application_approved': 'Congratulations! Application Approved',
            'application_rejected': 'Application Status Update',
            'credit_report_pulled': 'Credit Report Pulled',
            'preapproval_submitted': 'Pre-Approval Submitted',
            'preapproval_approved': 'Pre-Approval Approved',
            'preapproval_denied': 'Pre-Approval Status Update',
            'preapproval_letter_generated': 'Your Pre-Approval Letter is Ready',
            'document_processed': 'Document Processed Successfully',
            'welcome': 'Welcome to Mortgage Calculator',
        }
        return subjects.get(milestone, 'Mortgage Application Update')

    def _get_dashboard_url(self) -> str:
        """Get dashboard URL"""
        # In production, use actual domain from settings
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return f"{base_url}/dashboard"

    def _get_user_phone(self, user: User) -> Optional[str]:
        """Get user's phone number from profile"""
        try:
            # Check if user has profile with phone
            if hasattr(user, 'profile'):
                return getattr(user.profile, 'phone_number', None)
            return None
        except Exception:
            return None


# Global service instance
notification_service = NotificationService()
