# Notifications System

Email and SMS notification system for mortgage application milestones.

## Overview

This notification system provides:
- Email notifications with HTML templates
- SMS notifications with concise text messages
- Provider abstraction (Console, SMTP, SendGrid, Twilio, AWS SNS/SES)
- Async delivery via Celery tasks
- Audit logging with PII protection
- Rate limiting to prevent spam
- Automatic retry for failed notifications

## Key Milestones

Notifications are triggered for:

1. **Application Workflow**
   - `application_submitted` - Application submitted by borrower
   - `application_under_review` - Admin starts reviewing
   - `application_needs_correction` - Admin requests changes
   - `application_approved` - Application approved
   - `application_rejected` - Application rejected

2. **Credit & Pre-Approval**
   - `credit_report_pulled` - Credit report pulled
   - `preapproval_letter_generated` - Pre-approval letter ready

3. **User Events**
   - `welcome` - New user registration
   - `document_processed` - Document OCR completed

## Configuration

### Environment Variables

```bash
# Email Provider (console, smtp, sendgrid, ses, mailgun)
EMAIL_PROVIDER=console
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@mortgagecalculator.com

# SendGrid
SENDGRID_API_KEY=

# AWS SES
AWS_SES_REGION_NAME=us-east-1

# SMS Provider (console, twilio, sns)
SMS_PROVIDER=console

# Twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=+15551234567

# AWS SNS
AWS_SNS_REGION_NAME=us-east-1

# Notification Settings
NOTIFICATIONS_ENABLED=True
ENABLE_EMAIL_NOTIFICATIONS=True
ENABLE_SMS_NOTIFICATIONS=False  # Opt-in only

# Rate Limiting
NOTIFICATION_MAX_RETRIES=3
NOTIFICATION_RETRY_DELAY=300  # 5 minutes
NOTIFICATION_RATE_LIMIT_PER_USER=10  # per hour
```

### Development Setup (Console Mode)

By default, notifications use "console" mode which logs to stdout:

```bash
EMAIL_PROVIDER=console
SMS_PROVIDER=console
```

This is safe for development and doesn't send real emails/SMS.

## Usage

### Programmatic Sending

```python
from notifications.service import notification_service
from django.contrib.auth.models import User

user = User.objects.get(username='borrower')

# Send email
notification_service.send_email_notification(
    user=user,
    milestone='application_submitted',
    context={
        'application_id': 123,
        'property_address': '123 Main St',
        'loan_amount': '500,000',
        'submitted_date': 'January 1, 2025',
        'application_url': 'https://app.com/applications/123',
    }
)

# Send SMS
notification_service.send_sms_notification(
    user=user,
    milestone='application_approved',
    context={
        'loan_amount': '500,000',
        'short_url': 'https://app.com/a/123',
    },
    phone_number='+15551234567',  # Optional override
)
```

### Async Tasks (Recommended)

```python
from notifications.tasks import send_email_notification_task

# Queue email notification (async)
send_email_notification_task.delay(
    user_id=user.id,
    milestone='application_approved',
    context={...}
)
```

### Automatic Triggering (Signals)

Notifications are automatically sent when:

1. **User created** → Welcome email
2. **LoanEstimate status changes** → Status update email/SMS
3. **CreditReport pulled** → Credit pull notification
4. **PreApproval letter generated** → Letter ready notification

No manual intervention needed - signals handle it automatically.

## Email Templates

Templates are located in `notifications/templates/email/`:

- `base.html` - Base template with header/footer
- `application_submitted.html`
- `application_under_review.html`
- `application_needs_correction.html`
- `application_approved.html`
- `application_rejected.html`
- `credit_report_pulled.html`
- `preapproval_letter_generated.html`
- `welcome.html`

### Customizing Templates

Templates use Django template language:

```html
{% extends "email/base.html" %}

{% block header_title %}Custom Title{% endblock %}

{% block content %}
<p>Dear {{ borrower_name }},</p>
<p>Custom content here...</p>
{% endblock %}
```

## SMS Templates

SMS templates are in `notifications/templates/sms/templates.py`:

```python
SMS_TEMPLATES = {
    'application_submitted': (
        "Your mortgage application (ID: {application_id}) has been submitted..."
    ),
}
```

All SMS messages include opt-out language per TCPA compliance.

## Audit Logging

All notifications are logged to `NotificationLog` model:

```python
from notifications.models import NotificationLog

# Query logs
logs = NotificationLog.objects.filter(
    user=user,
    milestone='application_submitted',
    status='sent'
)

# Check delivery status
for log in logs:
    print(f"{log.milestone}: {log.status}")
    print(f"Sent: {log.sent_at}")
    print(f"Provider: {log.provider}")
```

### Admin Interface

View notification logs in Django Admin:
- `/admin/notifications/notificationlog/`

## Rate Limiting

Prevents notification spam:
- Default: 10 notifications per user per hour
- Configurable via `NOTIFICATION_RATE_LIMIT_PER_USER`
- Applies across email + SMS combined

## Retry Logic

Failed notifications are automatically retried:
- Max retries: 3 (configurable)
- Exponential backoff: 5min, 10min, 20min
- Periodic task runs every 30 minutes via Celery Beat

## Production Setup

### SendGrid (Email)

```bash
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your_api_key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### Twilio (SMS)

```bash
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+15551234567
ENABLE_SMS_NOTIFICATIONS=True
```

### AWS SES + SNS

```bash
# Email via SES
EMAIL_PROVIDER=ses
AWS_SES_REGION_NAME=us-east-1
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# SMS via SNS
SMS_PROVIDER=sns
AWS_SNS_REGION_NAME=us-east-1
```

## Testing

Run tests:

```bash
# All notification tests
python manage.py test notifications

# Specific test
python manage.py test notifications.tests.NotificationServiceTestCase
```

## Security & Compliance

### PII Protection
- Phone numbers masked in logs (***1234)
- Email addresses only shown to authorized staff
- No message content stored in logs (preview only)

### TCPA Compliance (SMS)
- All SMS include opt-out language ("Reply STOP")
- SMS disabled by default (opt-in required)
- User consent tracked

### GDPR Considerations
- Notification logs can be purged per user
- PII masked in audit trails
- User email preferences respected

## Monitoring

### Key Metrics
- Delivery rate: `sent / (sent + failed)`
- Error rate: `failed / total`
- Retry rate: `retry_count > 0 / total`

### Queries

```python
from notifications.models import NotificationLog
from django.db.models import Count

# Delivery stats
stats = NotificationLog.objects.values('status').annotate(count=Count('id'))

# Failed notifications
failed = NotificationLog.objects.filter(
    status='failed',
    error_message__isnull=False
).values('error_message').annotate(count=Count('id'))
```

## Troubleshooting

### Emails not sending

1. Check `NOTIFICATIONS_ENABLED=True`
2. Check `ENABLE_EMAIL_NOTIFICATIONS=True`
3. Verify email provider credentials
4. Check Celery worker is running
5. Review logs: `docker-compose logs backend`

### SMS not sending

1. Check `ENABLE_SMS_NOTIFICATIONS=True`
2. Verify SMS provider credentials
3. Ensure phone number in E.164 format (+15551234567)
4. Check user has phone number set

### Duplicate notifications

1. Check rate limiting settings
2. Verify signals not firing multiple times
3. Review recent `NotificationLog` entries

## Future Enhancements

- [ ] User notification preferences (email/SMS opt-in per milestone)
- [ ] Digest notifications (daily/weekly summaries)
- [ ] In-app notifications
- [ ] Push notifications (mobile app)
- [ ] A/B testing for templates
- [ ] Delivery analytics dashboard
- [ ] Webhook callbacks for delivery status
