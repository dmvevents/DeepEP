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
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")

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

    # Error handling
    error_message = models.TextField(blank=True)

    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.user.username} ({self.uploaded_at.date()})"
