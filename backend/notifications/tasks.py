"""
Celery tasks for sending notifications.
Async task queue for emails and SMS.
"""
from celery import shared_task
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
import logging

from .service import notification_service
from .models import NotificationLog
from api.models import AuditEvent

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=settings.NOTIFICATION_MAX_RETRIES)
def send_email_notification_task(
    self,
    user_id: int,
    milestone: str,
    context: dict,
    template_name: str = None,
):
    """
    Async task to send email notification.

    Args:
        user_id: User ID to notify
        milestone: Notification milestone
        context: Template context dict
        template_name: Optional template name
    """
    try:
        user = User.objects.get(id=user_id)
        notification_log = notification_service.send_email_notification(
            user=user,
            milestone=milestone,
            context=context,
            template_name=template_name,
        )

        # Create audit event for notification
        _create_notification_audit_event(user, 'email', milestone, notification_log)

        return {
            'success': notification_log.status == 'sent',
            'notification_id': notification_log.id,
            'status': notification_log.status,
        }

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for email notification")
        return {'success': False, 'error': 'User not found'}

    except Exception as e:
        logger.error(f"Email notification task failed: {str(e)}", exc_info=True)

        # Retry with exponential backoff
        retry_delay = settings.NOTIFICATION_RETRY_DELAY * (2 ** self.request.retries)
        raise self.retry(exc=e, countdown=retry_delay)


@shared_task(bind=True, max_retries=settings.NOTIFICATION_MAX_RETRIES)
def send_sms_notification_task(
    self,
    user_id: int,
    milestone: str,
    context: dict,
    phone_number: str = None,
):
    """
    Async task to send SMS notification.

    Args:
        user_id: User ID to notify
        milestone: Notification milestone
        context: Template context dict
        phone_number: Optional phone override
    """
    try:
        user = User.objects.get(id=user_id)
        notification_log = notification_service.send_sms_notification(
            user=user,
            milestone=milestone,
            context=context,
            phone_number=phone_number,
        )

        # Create audit event for notification
        _create_notification_audit_event(user, 'sms', milestone, notification_log)

        return {
            'success': notification_log.status == 'sent',
            'notification_id': notification_log.id,
            'status': notification_log.status,
        }

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for SMS notification")
        return {'success': False, 'error': 'User not found'}

    except Exception as e:
        logger.error(f"SMS notification task failed: {str(e)}", exc_info=True)

        # Retry with exponential backoff
        retry_delay = settings.NOTIFICATION_RETRY_DELAY * (2 ** self.request.retries)
        raise self.retry(exc=e, countdown=retry_delay)


@shared_task
def retry_failed_notifications():
    """
    Periodic task to retry failed notifications.
    Runs via Celery Beat.
    """
    retry_cutoff = timezone.now() - timezone.timedelta(hours=24)

    failed_notifications = NotificationLog.objects.filter(
        status='failed',
        retry_count__lt=settings.NOTIFICATION_MAX_RETRIES,
        created_at__gte=retry_cutoff,
    ).select_related('user')

    retry_count = 0
    for notification in failed_notifications:
        try:
            if notification.notification_type == 'email':
                # Re-extract context from log
                context = {
                    'borrower_name': notification.user.get_full_name() or notification.user.username,
                }
                send_email_notification_task.delay(
                    user_id=notification.user.id,
                    milestone=notification.milestone,
                    context=context,
                )
            elif notification.notification_type == 'sms':
                context = {}
                send_sms_notification_task.delay(
                    user_id=notification.user.id,
                    milestone=notification.milestone,
                    context=context,
                )

            notification.retry_count += 1
            notification.save()
            retry_count += 1

        except Exception as e:
            logger.error(f"Retry failed for notification {notification.id}: {str(e)}")

    logger.info(f"Retried {retry_count} failed notifications")
    return {
        'retried': retry_count,
        'timestamp': timezone.now().isoformat(),
    }


def _create_notification_audit_event(
    user: User,
    notification_type: str,
    milestone: str,
    notification_log: NotificationLog,
):
    """
    Create audit event for notification.

    Args:
        user: User who received notification
        notification_type: 'email' or 'sms'
        milestone: Notification milestone
        notification_log: NotificationLog instance
    """
    try:
        # Map milestone to audit event type (if applicable)
        event_type_map = {
            'credit_report_pulled': 'credit_pull',
            'application_submitted': 'application_submit',
            'application_approved': 'application_approve',
            'application_rejected': 'application_reject',
            'preapproval_letter_generated': 'preapproval_letter_generate',
        }

        # Only create audit event for specific milestones
        if milestone in event_type_map:
            AuditEvent.objects.create(
                event_type=event_type_map[milestone],
                user=user,
                borrower_name=user.get_full_name() or user.username,
                context={
                    'notification_sent': True,
                    'notification_type': notification_type,
                    'notification_id': notification_log.id,
                    'notification_status': notification_log.status,
                    'milestone': milestone,
                }
            )
    except Exception as e:
        logger.error(f"Failed to create audit event: {str(e)}")
