"""
SMS text templates for key milestones.
SMS messages must be concise (160 chars recommended) and include opt-out language.
"""

SMS_TEMPLATES = {
    'application_submitted': (
        "Your mortgage application (ID: {application_id}) has been submitted successfully. "
        "We'll review it within 24-48 hours. Check status: {short_url}"
    ),
    'application_under_review': (
        "Your mortgage application is now under review by {reviewer_name}. "
        "We'll notify you once complete. Status: {short_url}"
    ),
    'application_needs_correction': (
        "ACTION REQUIRED: Your mortgage application needs corrections. "
        "Please review feedback and update: {short_url}"
    ),
    'application_approved': (
        "CONGRATULATIONS! Your mortgage application for ${loan_amount} has been APPROVED! "
        "View details: {short_url}"
    ),
    'application_rejected': (
        "Your mortgage application status has been updated. "
        "Please log in to review details and next steps: {short_url}"
    ),
    'credit_report_pulled': (
        "We've pulled your credit report for your mortgage application. "
        "If you didn't authorize this, contact us immediately."
    ),
    'preapproval_letter_generated': (
        "Your pre-approval letter is ready! Max purchase: ${max_purchase_price}. "
        "Download now: {short_url}"
    ),
    'welcome': (
        "Welcome to Mortgage Calculator! Your account is ready. "
        "Start your application: {short_url}"
    ),
}

# Footer appended to all SMS (TCPA compliance)
SMS_FOOTER = " Reply STOP to unsubscribe."


def get_sms_template(milestone: str) -> str:
    """Get SMS template for milestone"""
    return SMS_TEMPLATES.get(milestone, "")


def render_sms_message(milestone: str, context: dict) -> str:
    """
    Render SMS message with context variables.

    Args:
        milestone: Notification milestone key
        context: Dictionary of variables to substitute

    Returns:
        Rendered SMS message with footer
    """
    template = get_sms_template(milestone)
    if not template:
        raise ValueError(f"Unknown SMS milestone: {milestone}")

    try:
        message = template.format(**context)
        return message + SMS_FOOTER
    except KeyError as e:
        raise ValueError(f"Missing context variable: {e}")
