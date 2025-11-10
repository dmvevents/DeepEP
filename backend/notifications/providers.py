"""
Email and SMS provider abstraction layer.
Supports multiple providers with consistent interface.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import datetime

logger = logging.getLogger(__name__)


class EmailProvider(ABC):
    """Abstract base class for email providers"""

    @abstractmethod
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an email.

        Returns:
            dict with keys: success (bool), message_id (str), error (str)
        """
        pass


class ConsoleEmailProvider(EmailProvider):
    """Console email provider for development"""

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log email to console"""
        from_email = from_email or settings.DEFAULT_FROM_EMAIL

        logger.info(f"[CONSOLE EMAIL] To: {to_email}")
        logger.info(f"[CONSOLE EMAIL] From: {from_email}")
        logger.info(f"[CONSOLE EMAIL] Subject: {subject}")
        logger.info(f"[CONSOLE EMAIL] HTML Length: {len(html_content)} chars")

        try:
            # Django console backend will print to stdout
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content or strip_tags(html_content),
                from_email=from_email,
                to=[to_email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            return {
                'success': True,
                'message_id': f'console-{datetime.datetime.now().timestamp()}',
                'error': '',
            }
        except Exception as e:
            logger.error(f"Console email failed: {str(e)}")
            return {
                'success': False,
                'message_id': '',
                'error': str(e),
            }


class SMTPEmailProvider(EmailProvider):
    """SMTP email provider (Django default)"""

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send via SMTP"""
        from_email = from_email or settings.DEFAULT_FROM_EMAIL

        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content or strip_tags(html_content),
                from_email=from_email,
                to=[to_email],
            )
            email.attach_alternative(html_content, "text/html")
            result = email.send()

            if result:
                logger.info(f"Email sent to {to_email}: {subject}")
                return {
                    'success': True,
                    'message_id': f'smtp-{datetime.datetime.now().timestamp()}',
                    'error': '',
                }
            else:
                return {
                    'success': False,
                    'message_id': '',
                    'error': 'SMTP send returned 0',
                }
        except Exception as e:
            logger.error(f"SMTP email failed: {str(e)}")
            return {
                'success': False,
                'message_id': '',
                'error': str(e),
            }


class SendGridEmailProvider(EmailProvider):
    """SendGrid email provider"""

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send via SendGrid"""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content

            from_email_obj = Email(from_email or settings.DEFAULT_FROM_EMAIL)
            to_email_obj = To(to_email)
            content = Content("text/html", html_content)

            mail = Mail(from_email_obj, to_email_obj, subject, content)

            sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            response = sg.send(mail)

            logger.info(f"SendGrid email sent to {to_email}: {subject}")
            return {
                'success': response.status_code in [200, 201, 202],
                'message_id': response.headers.get('X-Message-Id', ''),
                'error': '' if response.status_code in [200, 201, 202] else f"Status {response.status_code}",
            }
        except Exception as e:
            logger.error(f"SendGrid email failed: {str(e)}")
            return {
                'success': False,
                'message_id': '',
                'error': str(e),
            }


class SMSProvider(ABC):
    """Abstract base class for SMS providers"""

    @abstractmethod
    def send_sms(
        self,
        to_phone: str,
        message: str,
        from_phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an SMS.

        Args:
            to_phone: Recipient phone in E.164 format (+15551234567)
            message: SMS message text
            from_phone: Sender phone (optional)

        Returns:
            dict with keys: success (bool), message_id (str), error (str)
        """
        pass


class ConsoleSMSProvider(SMSProvider):
    """Console SMS provider for development"""

    def send_sms(
        self,
        to_phone: str,
        message: str,
        from_phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log SMS to console"""
        from_phone = from_phone or settings.TWILIO_FROM_NUMBER or '+15555555555'

        logger.info(f"[CONSOLE SMS] To: {to_phone}")
        logger.info(f"[CONSOLE SMS] From: {from_phone}")
        logger.info(f"[CONSOLE SMS] Message: {message}")

        return {
            'success': True,
            'message_id': f'console-sms-{datetime.datetime.now().timestamp()}',
            'error': '',
        }


class TwilioSMSProvider(SMSProvider):
    """Twilio SMS provider"""

    def send_sms(
        self,
        to_phone: str,
        message: str,
        from_phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send via Twilio"""
        try:
            from twilio.rest import Client

            client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )

            from_phone = from_phone or settings.TWILIO_FROM_NUMBER

            message_obj = client.messages.create(
                body=message,
                from_=from_phone,
                to=to_phone
            )

            logger.info(f"Twilio SMS sent to {to_phone}")
            return {
                'success': True,
                'message_id': message_obj.sid,
                'error': '',
            }
        except Exception as e:
            logger.error(f"Twilio SMS failed: {str(e)}")
            return {
                'success': False,
                'message_id': '',
                'error': str(e),
            }


class AWSSNSProvider(SMSProvider):
    """AWS SNS SMS provider"""

    def send_sms(
        self,
        to_phone: str,
        message: str,
        from_phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send via AWS SNS"""
        try:
            import boto3

            sns = boto3.client(
                'sns',
                region_name=settings.AWS_SNS_REGION_NAME
            )

            response = sns.publish(
                PhoneNumber=to_phone,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )

            logger.info(f"AWS SNS SMS sent to {to_phone}")
            return {
                'success': True,
                'message_id': response.get('MessageId', ''),
                'error': '',
            }
        except Exception as e:
            logger.error(f"AWS SNS SMS failed: {str(e)}")
            return {
                'success': False,
                'message_id': '',
                'error': str(e),
            }


# Provider factory functions
def get_email_provider() -> EmailProvider:
    """Get configured email provider"""
    provider = getattr(settings, 'EMAIL_PROVIDER', 'console')

    providers = {
        'console': ConsoleEmailProvider,
        'smtp': SMTPEmailProvider,
        'sendgrid': SendGridEmailProvider,
    }

    provider_class = providers.get(provider, ConsoleEmailProvider)
    return provider_class()


def get_sms_provider() -> SMSProvider:
    """Get configured SMS provider"""
    provider = getattr(settings, 'SMS_PROVIDER', 'console')

    providers = {
        'console': ConsoleSMSProvider,
        'twilio': TwilioSMSProvider,
        'sns': AWSSNSProvider,
    }

    provider_class = providers.get(provider, ConsoleSMSProvider)
    return provider_class()
