"""
Audit logging utilities for document operations.
"""
from typing import Optional, Dict, Any
from django.contrib.auth.models import User
from api.models import AuditEvent, LoanEstimate
import logging

logger = logging.getLogger(__name__)


def log_document_event(
    event_type: str,
    user: User,
    document_id: int,
    loan_estimate: Optional[LoanEstimate] = None,
    context: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuditEvent:
    """
    Log a document-related audit event.

    Args:
        event_type: Type of event (document_upload, document_scan, etc.)
        user: User who triggered the event
        document_id: ID of the DocumentUpload
        loan_estimate: Optional associated loan application
        context: Additional context data
        ip_address: Client IP address
        user_agent: Client user agent

    Returns:
        Created AuditEvent instance
    """
    if context is None:
        context = {}

    # Add document_id to context
    context['document_id'] = document_id

    try:
        audit_event = AuditEvent.objects.create(
            event_type=event_type,
            user=user,
            borrower_name=user.get_full_name() or user.username,
            loan_estimate=loan_estimate,
            ip_address=ip_address,
            user_agent=user_agent or '',
            context=context
        )
        logger.info(
            f"Audit event logged: {event_type} for user {user.username}, "
            f"document_id={document_id}"
        )
        return audit_event

    except Exception as e:
        logger.error(f"Failed to log audit event: {str(e)}", exc_info=True)
        raise


def extract_client_ip(request) -> Optional[str]:
    """
    Extract client IP from request, considering proxies.

    Args:
        request: Django request object

    Returns:
        Client IP address or None
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP in the chain
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def extract_user_agent(request) -> str:
    """
    Extract user agent from request.

    Args:
        request: Django request object

    Returns:
        User agent string
    """
    return request.META.get('HTTP_USER_AGENT', '')
