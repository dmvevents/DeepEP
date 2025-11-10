"""
Celery tasks for document processing
"""
from celery import shared_task
from django.utils import timezone
from django.conf import settings
import logging
import requests
import os

from .models import DocumentUpload
from .virus_scan import virus_scanner
from .audit import log_document_event
from api.models import DocTask

logger = logging.getLogger(__name__)


@shared_task
def scan_document(document_id):
    """
    Perform virus scan on uploaded document.
    Called immediately after upload, before OCR processing.
    """
    try:
        document = DocumentUpload.objects.get(id=document_id)
        document.status = 'scanning'
        document.save()

        logger.info(f"Scanning document {document_id}: {document.file_name}")

        # Get file path
        file_path = document.file.path

        # Perform virus scan
        scan_result = virus_scanner.scan_file(file_path)

        # Update document with scan results
        document.virus_scan_result = scan_result
        document.detected_mime_type = scan_result.get('mime_type', '')
        document.scanned_at = timezone.now()

        if scan_result['safe']:
            document.virus_scan_passed = True
            document.status = 'uploaded'  # Ready for OCR
            logger.info(f"Document {document_id} passed virus scan")

            # Log audit event
            try:
                log_document_event(
                    event_type='document_scan',
                    user=document.user,
                    document_id=document_id,
                    loan_estimate=document.loan_estimate,
                    context={
                        'scan_result': 'passed',
                        'mime_type': scan_result.get('mime_type'),
                        'scanned': scan_result.get('scanned', False)
                    }
                )
            except Exception as audit_err:
                logger.error(f"Failed to log audit event: {str(audit_err)}")

            # Trigger OCR processing
            process_document.delay(document_id)
        else:
            document.virus_scan_passed = False
            document.status = 'rejected'
            document.error_message = scan_result.get('reason', 'Security check failed')
            logger.warning(f"Document {document_id} rejected: {document.error_message}")

            # Log audit event
            try:
                log_document_event(
                    event_type='document_rejected',
                    user=document.user,
                    document_id=document_id,
                    loan_estimate=document.loan_estimate,
                    context={
                        'reason': document.error_message,
                        'mime_type': scan_result.get('mime_type')
                    }
                )
            except Exception as audit_err:
                logger.error(f"Failed to log audit event: {str(audit_err)}")

        document.save()

    except DocumentUpload.DoesNotExist:
        logger.error(f"Document {document_id} not found")
    except Exception as e:
        logger.error(f"Document scanning failed: {str(e)}", exc_info=True)
        try:
            document.status = 'failed'
            document.error_message = f"Scan failed: {str(e)}"
            document.save()
        except:
            pass


@shared_task
def process_document(document_id):
    """
    Process document with OCR and extraction.
    Integrates with OCR service and updates associated DocTask.
    """
    try:
        document = DocumentUpload.objects.get(id=document_id)
        document.status = 'processing'
        document.save()

        logger.info(f"Processing document {document_id}: {document.file_name}")

        # Call OCR service
        ocr_service_url = getattr(settings, 'OCR_SERVICE_URL', 'http://localhost:8003')

        # Check if file exists
        if not os.path.exists(document.file.path):
            raise FileNotFoundError(f"Document file not found: {document.file.path}")

        with open(document.file.path, 'rb') as f:
            files = {'file': (document.file_name, f, document.detected_mime_type or 'application/pdf')}
            data = {'document_type': document.document_type}

            try:
                response = requests.post(
                    f'{ocr_service_url}/extract',
                    files=files,
                    data=data,
                    timeout=60
                )
                response.raise_for_status()
                ocr_result = response.json()

                # Update document with OCR results
                document.ocr_text = ocr_result.get('text', '')
                document.extracted_data = ocr_result.get('structured_data', {})
                document.extraction_confidence = ocr_result.get('confidence', 0)
                document.status = 'completed'
                document.processed_at = timezone.now()

                logger.info(f"Document {document_id} processed successfully (confidence: {document.extraction_confidence})")

                # Update associated DocTask if exists
                if document.doc_task:
                    update_doc_task_from_ocr.delay(document.doc_task.id, document_id, document.extracted_data)

                # Log audit event
                try:
                    log_document_event(
                        event_type='document_ocr',
                        user=document.user,
                        document_id=document_id,
                        loan_estimate=document.loan_estimate,
                        context={
                            'confidence': document.extraction_confidence,
                            'document_type': document.document_type,
                            'extracted_fields': list(document.extracted_data.keys()) if document.extracted_data else []
                        }
                    )
                except Exception as audit_err:
                    logger.error(f"Failed to log audit event: {str(audit_err)}")

            except requests.exceptions.RequestException as req_err:
                # OCR service unavailable - log but don't fail
                logger.warning(f"OCR service unavailable for document {document_id}: {str(req_err)}")
                document.ocr_text = ""
                document.extracted_data = {"message": "OCR service unavailable", "document_type": document.document_type}
                document.extraction_confidence = 0
                document.status = 'completed'  # Mark as completed even if OCR failed
                document.processed_at = timezone.now()

        document.save()

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
def update_doc_task_from_ocr(doc_task_id, document_id, extracted_data):
    """
    OCR webhook: Update DocTask with extracted data from document.

    Args:
        doc_task_id: ID of DocTask to update
        document_id: ID of DocumentUpload that was processed
        extracted_data: Structured data extracted from OCR
    """
    try:
        doc_task = DocTask.objects.get(id=doc_task_id)

        # Update task's uploaded_documents list
        if not doc_task.uploaded_documents:
            doc_task.uploaded_documents = []

        if document_id not in doc_task.uploaded_documents:
            doc_task.uploaded_documents.append(document_id)

        # If all required documents uploaded, mark task as completed
        # (This logic can be enhanced based on task type)
        if doc_task.status == 'pending':
            doc_task.status = 'in_progress'

        # Check if we have sufficient data to auto-complete
        if extracted_data and doc_task.status == 'in_progress':
            # For verify_income tasks, check if we extracted income
            if doc_task.task_type == 'verify_income' and 'annual_income' in extracted_data:
                doc_task.status = 'completed'
                doc_task.completed_at = timezone.now()
                doc_task.borrower_notes = f"Automatically verified from document. Annual income: ${extracted_data['annual_income']}"

            # For verify_assets tasks, check if we extracted account balance
            elif doc_task.task_type == 'verify_assets' and 'account_balance' in extracted_data:
                doc_task.status = 'completed'
                doc_task.completed_at = timezone.now()
                doc_task.borrower_notes = f"Automatically verified from document. Account balance: ${extracted_data['account_balance']}"

        doc_task.save()
        logger.info(f"Updated DocTask {doc_task_id} with document {document_id} (status: {doc_task.status})")

    except DocTask.DoesNotExist:
        logger.error(f"DocTask {doc_task_id} not found")
    except Exception as e:
        logger.error(f"Failed to update DocTask {doc_task_id}: {str(e)}", exc_info=True)


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
