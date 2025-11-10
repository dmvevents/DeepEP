"""
Django signals to trigger notifications on workflow state changes.
Connects model changes to notification tasks.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.conf import settings

from api.models import LoanEstimate, PreApproval, CreditReport
from documents.models import DocumentUpload
from .tasks import send_email_notification_task, send_sms_notification_task

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def send_welcome_notification(sender, instance, created, **kwargs):
    """Send welcome notification when user is created"""
    if created and settings.NOTIFICATIONS_ENABLED:
        logger.info(f"Sending welcome notification to user {instance.id}")

        context = {
            'borrower_name': instance.get_full_name() or instance.username,
            'username': instance.username,
            'email': instance.email,
            'created_date': instance.date_joined.strftime('%B %d, %Y'),
            'dashboard_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/dashboard",
        }

        # Send email (async)
        send_email_notification_task.delay(
            user_id=instance.id,
            milestone='welcome',
            context=context,
        )


@receiver(pre_save, sender=LoanEstimate)
def track_loan_estimate_status_change(sender, instance, **kwargs):
    """Track LoanEstimate status changes to trigger notifications"""
    if instance.pk:  # Existing object
        try:
            old_instance = LoanEstimate.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except LoanEstimate.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=LoanEstimate)
def send_loan_estimate_notifications(sender, instance, created, **kwargs):
    """Send notifications when LoanEstimate status changes"""
    if not settings.NOTIFICATIONS_ENABLED:
        return

    # Get old status from pre_save signal
    old_status = getattr(instance, '_old_status', None)
    new_status = instance.status

    # Skip if status hasn't changed
    if old_status == new_status and not created:
        return

    # Common context for all notifications
    base_context = {
        'borrower_name': instance.user.get_full_name() or instance.user.username,
        'application_id': instance.id,
        'property_address': instance.property_address or 'Not specified',
        'loan_amount': f"{instance.loan_amount:,.0f}",
        'application_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/applications/{instance.id}",
    }

    # Determine milestone based on status
    milestone = None
    context = base_context.copy()

    if new_status == 'submitted':
        milestone = 'application_submitted'
        context['submitted_date'] = instance.submitted_at.strftime('%B %d, %Y') if instance.submitted_at else 'Today'

    elif new_status == 'under_review':
        milestone = 'application_under_review'
        context['reviewer_name'] = instance.reviewed_by.get_full_name() if instance.reviewed_by else 'Our team'
        context['review_date'] = instance.reviewed_at.strftime('%B %d, %Y') if instance.reviewed_at else 'Today'

    elif new_status == 'needs_correction':
        milestone = 'application_needs_correction'
        context['admin_feedback'] = instance.admin_feedback or 'Please review your application.'

    elif new_status == 'approved':
        milestone = 'application_approved'
        context['approval_date'] = instance.reviewed_at.strftime('%B %d, %Y') if instance.reviewed_at else 'Today'

    elif new_status == 'rejected':
        milestone = 'application_rejected'
        context['decision_date'] = instance.reviewed_at.strftime('%B %d, %Y') if instance.reviewed_at else 'Today'
        context['admin_feedback'] = instance.admin_feedback or 'Please contact us for more information.'

    # Send notifications if milestone identified
    if milestone:
        logger.info(f"Sending {milestone} notification for LoanEstimate {instance.id}")

        # Send email
        send_email_notification_task.delay(
            user_id=instance.user.id,
            milestone=milestone,
            context=context,
        )

        # Send SMS if enabled and user has opted in
        if settings.ENABLE_SMS_NOTIFICATIONS:
            context['short_url'] = context['application_url']  # In production, use URL shortener
            send_sms_notification_task.delay(
                user_id=instance.user.id,
                milestone=milestone,
                context=context,
            )


@receiver(post_save, sender=CreditReport)
def send_credit_report_notification(sender, instance, created, **kwargs):
    """Send notification when credit report is pulled"""
    if created and instance.status == 'pulled' and settings.NOTIFICATIONS_ENABLED:
        logger.info(f"Sending credit report notification for user {instance.user.id}")

        context = {
            'borrower_name': instance.user.get_full_name() or instance.user.username,
            'bureau': instance.get_bureau_display(),
            'report_date': instance.report_date.strftime('%B %d, %Y'),
            'application_id': instance.loan_estimate.id if instance.loan_estimate else 'N/A',
            'application_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/dashboard",
        }

        # Send email
        send_email_notification_task.delay(
            user_id=instance.user.id,
            milestone='credit_report_pulled',
            context=context,
        )

        # Send SMS if enabled
        if settings.ENABLE_SMS_NOTIFICATIONS:
            send_sms_notification_task.delay(
                user_id=instance.user.id,
                milestone='credit_report_pulled',
                context=context,
            )


@receiver(post_save, sender=PreApproval)
def send_preapproval_notifications(sender, instance, created, **kwargs):
    """Send notifications for pre-approval status changes"""
    if not settings.NOTIFICATIONS_ENABLED:
        return

    milestone = None
    context = {
        'borrower_name': instance.borrower_name,
        'preapproval_id': instance.id,
        'max_purchase_price': f"{instance.max_purchase_price:,.0f}",
        'max_loan_amount': f"{instance.max_loan_amount:,.0f}",
        'expiration_date': instance.expiration_date.strftime('%B %d, %Y'),
    }

    # Detect milestone based on letter generation
    if instance.letter_generated_at and not created:
        # Check if letter was just generated
        try:
            old_instance = PreApproval.objects.get(pk=instance.pk)
            if not old_instance.letter_generated_at and instance.letter_generated_at:
                milestone = 'preapproval_letter_generated'
                context['letter_download_url'] = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/preapprovals/{instance.id}/letter"
        except PreApproval.DoesNotExist:
            pass

    # Send notifications if milestone identified
    if milestone:
        logger.info(f"Sending {milestone} notification for PreApproval {instance.id}")

        # Send to borrower (use borrower_email if available, else user)
        if instance.user:
            send_email_notification_task.delay(
                user_id=instance.user.id,
                milestone=milestone,
                context=context,
            )

            if settings.ENABLE_SMS_NOTIFICATIONS:
                context['short_url'] = context.get('letter_download_url', '')
                send_sms_notification_task.delay(
                    user_id=instance.user.id,
                    milestone=milestone,
                    context=context,
                )


@receiver(post_save, sender=DocumentUpload)
def send_document_notification(sender, instance, created, **kwargs):
    """Send notification when document processing completes"""
    if not created and instance.status == 'completed' and settings.NOTIFICATIONS_ENABLED:
        # Only notify if status changed to completed
        try:
            old_instance = DocumentUpload.objects.get(pk=instance.pk)
            if old_instance.status != 'completed':
                logger.info(f"Sending document processed notification for document {instance.id}")

                context = {
                    'borrower_name': instance.user.get_full_name() or instance.user.username,
                    'document_type': instance.get_document_type_display(),
                    'file_name': instance.file_name,
                    'confidence': instance.extraction_confidence or 0,
                    'application_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/dashboard",
                }

                # Send email
                send_email_notification_task.delay(
                    user_id=instance.user.id,
                    milestone='document_processed',
                    context=context,
                )
        except DocumentUpload.DoesNotExist:
            pass
