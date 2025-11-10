"""
Notification tracking models
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class NotificationLog(models.Model):
    """
    Audit log for all notifications sent (email/SMS).
    Tracks delivery status and errors for compliance.
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('delivered', 'Delivered'),
    ]

    MILESTONE_CHOICES = [
        ('application_submitted', 'Application Submitted'),
        ('application_under_review', 'Application Under Review'),
        ('application_needs_correction', 'Application Needs Correction'),
        ('application_approved', 'Application Approved'),
        ('application_rejected', 'Application Rejected'),
        ('credit_report_pulled', 'Credit Report Pulled'),
        ('preapproval_submitted', 'Pre-Approval Submitted'),
        ('preapproval_approved', 'Pre-Approval Approved'),
        ('preapproval_denied', 'Pre-Approval Denied'),
        ('preapproval_letter_generated', 'Pre-Approval Letter Generated'),
        ('document_processed', 'Document Processed'),
        ('welcome', 'Welcome Email'),
    ]

    # Notification metadata
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPE_CHOICES)
    milestone = models.CharField(max_length=50, choices=MILESTONE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Recipient information (PII - masked in logs)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)  # E.164 format

    # Content
    subject = models.CharField(max_length=200, blank=True)
    message_preview = models.CharField(
        max_length=200,
        help_text="First 200 chars of message for audit trail"
    )

    # Related objects
    loan_estimate_id = models.IntegerField(null=True, blank=True)
    preapproval_id = models.IntegerField(null=True, blank=True)
    document_id = models.IntegerField(null=True, blank=True)

    # Provider information
    provider = models.CharField(
        max_length=50,
        help_text="Email/SMS provider used (e.g., 'console', 'sendgrid', 'twilio')"
    )
    provider_message_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="External provider's message ID for tracking"
    )

    # Delivery tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['milestone', '-created_at']),
            models.Index(fields=['status', 'retry_count']),
            models.Index(fields=['provider_message_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        recipient = self.recipient_email or self.recipient_phone or 'Unknown'
        return f"{self.get_milestone_display()} - {recipient} ({self.status})"
