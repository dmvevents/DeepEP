"""
Celery tasks for document processing
"""
from celery import shared_task
from django.utils import timezone
from django.conf import settings
import logging

from .models import DocumentUpload

logger = logging.getLogger(__name__)


@shared_task
def process_document(document_id):
    """
    Process document with OCR and extraction

    This is a placeholder for full OCR implementation
    """
    try:
        document = DocumentUpload.objects.get(id=document_id)
        document.status = 'processing'
        document.save()

        logger.info(f"Processing document {document_id}: {document.file_name}")

        # TODO: Implement actual OCR processing
        # 1. Extract text using Tesseract or DeepSeek OCR
        # 2. Send to LLM for structured extraction
        # 3. Validate and save extracted data

        # Placeholder response
        document.ocr_text = "OCR processing not yet implemented"
        document.extracted_data = {
            "message": "OCR pipeline to be implemented",
            "document_type": document.document_type
        }
        document.extraction_confidence = 0
        document.status = 'completed'
        document.processed_at = timezone.now()
        document.save()

        logger.info(f"Document {document_id} processed successfully")

    except DocumentUpload.DoesNotExist:
        logger.error(f"Document {document_id} not found")
    except Exception as e:
        logger.error(f"Document processing failed: {str(e)}", exc_info=True)
        try:
            document.status = 'failed'
            document.error_message = str(e)
            document.processed_at = timezone.now()
            document.save()
        except:
            pass


@shared_task
def cleanup_old_documents():
    """
    Periodic task to cleanup old documents

    Runs weekly via Celery Beat
    """
    from datetime import timedelta

    # Delete documents older than 90 days
    cutoff_date = timezone.now() - timedelta(days=90)

    old_documents = DocumentUpload.objects.filter(
        uploaded_at__lt=cutoff_date
    )

    count = old_documents.count()
    logger.info(f"Cleaning up {count} old documents")

    # Delete files and records
    for doc in old_documents:
        try:
            if doc.file:
                doc.file.delete()
            doc.delete()
        except Exception as e:
            logger.error(f"Failed to delete document {doc.id}: {str(e)}")

    return {
        'cleaned_at': timezone.now().isoformat(),
        'documents_deleted': count
    }
