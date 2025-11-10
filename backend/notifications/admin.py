"""
Django admin for notifications
"""
from django.contrib import admin
from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """Admin interface for notification logs"""

    list_display = [
        'id',
        'milestone',
        'notification_type',
        'status',
        'recipient_display',
        'user',
        'provider',
        'sent_at',
        'created_at',
    ]
    list_filter = [
        'notification_type',
        'status',
        'milestone',
        'provider',
        'created_at',
    ]
    search_fields = [
        'recipient_email',
        'recipient_phone',
        'user__username',
        'user__email',
        'subject',
        'message_preview',
    ]
    readonly_fields = [
        'notification_type',
        'milestone',
        'status',
        'user',
        'recipient_email',
        'recipient_phone',
        'subject',
        'message_preview',
        'provider',
        'provider_message_id',
        'sent_at',
        'delivered_at',
        'error_message',
        'retry_count',
        'created_at',
        'updated_at',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def recipient_display(self, obj):
        """Display recipient (email or phone)"""
        if obj.notification_type == 'email':
            return obj.recipient_email
        elif obj.notification_type == 'sms':
            # Mask phone number for privacy
            phone = obj.recipient_phone
            if phone and len(phone) > 4:
                return f"***{phone[-4:]}"
            return phone
        return '-'
    recipient_display.short_description = 'Recipient'

    def has_add_permission(self, request):
        """Disable manual creation"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete"""
        return request.user.is_superuser
