"""
Document processing models
"""
from django.db import models
from django.contrib.auth.models import User


class DocumentUpload(models.Model):
    """User-uploaded documents for OCR processing"""

    DOCUMENT_TYPE_CHOICES = [
        ('pay_stub', 'Pay Stub'),
        ('w2', 'W-2 Form'),
        ('bank_statement', 'Bank Statement'),
        ('tax_return', 'Tax Return'),
        ('purchase_agreement', 'Purchase Agreement'),
        ('insurance', 'Insurance Declaration'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('scanning', 'Virus Scanning'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('rejected', 'Rejected (Security)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")

    # Doc-to-task linkage
    doc_task = models.ForeignKey(
        'api.DocTask',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='document_uploads',
        help_text="Associated document task this upload fulfills"
    )
    loan_estimate = models.ForeignKey(
        'api.LoanEstimate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supporting_documents',
        help_text="Associated loan application"
    )

    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    ocr_text = models.TextField(blank=True, help_text="Raw OCR output")
    extracted_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Structured data extracted by LLM"
    )
    extraction_confidence = models.IntegerField(
        null=True,
        blank=True,
        help_text="Confidence score 0-100"
    )

    # Virus scan results
    virus_scan_passed = models.BooleanField(
        null=True,
        blank=True,
        help_text="True if virus scan passed, False if failed, None if not scanned"
    )
    virus_scan_result = models.JSONField(
        null=True,
        blank=True,
        help_text="Full virus scan result details"
    )
    detected_mime_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="MIME type detected during upload"
    )

    # Error handling
    error_message = models.TextField(blank=True)

    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    scanned_at = models.DateTimeField(null=True, blank=True, help_text="When virus scan completed")

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', '-uploaded_at']),
            models.Index(fields=['doc_task']),
            models.Index(fields=['loan_estimate']),
            models.Index(fields=['status', '-uploaded_at']),
        ]

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.user.username} ({self.uploaded_at.date()})"
