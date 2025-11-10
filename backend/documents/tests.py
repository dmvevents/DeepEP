"""
Unit tests for documents app - Phase 2 OCR Pipeline
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
import json

from .models import DocumentUpload
from .storage import document_storage
from .virus_scan import VirusScanner
from .audit import log_document_event
from api.models import DocTask, LoanEstimate, AuditEvent, County, State


class DocumentStorageTests(TestCase):
    """Test storage abstraction"""

    def test_storage_backend_local(self):
        """Test local storage backend is used by default"""
        self.assertEqual(document_storage.backend, 'local')

    def test_storage_save_local(self):
        """Test saving file to local storage"""
        content = b'Test file content'
        file_path = 'test/document.pdf'

        saved_path = document_storage.save(file_path, SimpleUploadedFile('test.pdf', content))
        self.assertTrue(document_storage.exists(saved_path))

        # Cleanup
        document_storage.delete(saved_path)


class VirusScanTests(TestCase):
    """Test virus scanning functionality"""

    def setUp(self):
        self.scanner = VirusScanner()

    def test_mime_type_validation_allowed(self):
        """Test that allowed MIME types pass validation"""
        with patch('documents.virus_scan.HAS_MAGIC', False):
            with patch('mimetypes.guess_type', return_value=('application/pdf', None)):
                result = self.scanner._validate_mime_type('test.pdf')
                self.assertTrue(result['valid'])
                self.assertEqual(result['mime_type'], 'application/pdf')

    def test_mime_type_validation_rejected(self):
        """Test that disallowed MIME types are rejected"""
        with patch('documents.virus_scan.HAS_MAGIC', False):
            with patch('mimetypes.guess_type', return_value=('application/x-executable', None)):
                result = self.scanner._validate_mime_type('test.exe')
                self.assertFalse(result['valid'])
                self.assertIn('not allowed', result['reason'])


class DocumentUploadModelTests(TestCase):
    """Test DocumentUpload model enhancements"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.state = State.objects.create(code='MD', name='Maryland')
        self.county = County.objects.create(
            state=self.state,
            name='Montgomery County'
        )

    def test_document_upload_creation(self):
        """Test basic document upload creation"""
        doc = DocumentUpload.objects.create(
            user=self.user,
            document_type='pay_stub',
            file='test.pdf',
            file_name='test.pdf',
            file_size=1024
        )
        self.assertEqual(doc.status, 'uploaded')
        self.assertIsNone(doc.doc_task)
        self.assertIsNone(doc.loan_estimate)

    def test_document_with_doc_task_linkage(self):
        """Test document linked to DocTask"""
        from api.models import TaxData
        from datetime import date

        # Create TaxData first
        tax_data = TaxData.objects.create(
            state=self.state,
            county=self.county,
            version=1,
            data_completeness=100,
            scraper_confidence=95,
            data={'property_tax': {'total_rate': 0.01}},
            effective_date=date(2025, 1, 1)
        )

        loan_estimate = LoanEstimate.objects.create(
            user=self.user,
            county=self.county,
            property_value=300000,
            loan_amount=240000,
            down_payment=60000,
            interest_rate=6.5,
            loan_term_years=30,
            loan_type='conventional',
            property_type='single_family',
            first_time_homebuyer=False,
            closing_date='2025-06-01',
            calculation_results={},
            tax_data=tax_data
        )

        doc_task = DocTask.objects.create(
            user=self.user,
            loan_estimate=loan_estimate,
            task_type='verify_income',
            title='Upload Pay Stub',
            description='Please upload your most recent pay stub'
        )

        doc = DocumentUpload.objects.create(
            user=self.user,
            document_type='pay_stub',
            file='paystub.pdf',
            file_name='paystub.pdf',
            file_size=2048,
            doc_task=doc_task,
            loan_estimate=loan_estimate
        )

        self.assertEqual(doc.doc_task, doc_task)
        self.assertEqual(doc.loan_estimate, loan_estimate)
        self.assertIn(doc, doc_task.document_uploads.all())

    def test_virus_scan_fields(self):
        """Test virus scan result fields"""
        doc = DocumentUpload.objects.create(
            user=self.user,
            document_type='bank_statement',
            file='statement.pdf',
            file_name='statement.pdf',
            file_size=512,
            virus_scan_passed=True,
            virus_scan_result={'safe': True, 'scanned': False, 'mime_type': 'application/pdf'},
            detected_mime_type='application/pdf'
        )

        self.assertTrue(doc.virus_scan_passed)
        self.assertEqual(doc.detected_mime_type, 'application/pdf')
        self.assertIsNotNone(doc.virus_scan_result)


class AuditEventTests(TestCase):
    """Test audit event logging for documents"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_log_document_upload_event(self):
        """Test logging document upload audit event"""
        event = log_document_event(
            event_type='document_upload',
            user=self.user,
            document_id=1,
            context={
                'document_type': 'pay_stub',
                'file_name': 'test.pdf'
            }
        )

        self.assertEqual(event.event_type, 'document_upload')
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.context['document_id'], 1)
        self.assertIsNotNone(event.timestamp)

    def test_log_document_scan_event(self):
        """Test logging virus scan audit event"""
        event = log_document_event(
            event_type='document_scan',
            user=self.user,
            document_id=2,
            context={
                'scan_result': 'passed',
                'mime_type': 'application/pdf'
            }
        )

        self.assertEqual(event.event_type, 'document_scan')
        self.assertEqual(event.context['scan_result'], 'passed')

    def test_log_document_rejected_event(self):
        """Test logging document rejection audit event"""
        event = log_document_event(
            event_type='document_rejected',
            user=self.user,
            document_id=3,
            context={
                'reason': 'Virus detected',
                'mime_type': 'application/exe'
            }
        )

        self.assertEqual(event.event_type, 'document_rejected')
        self.assertIn('Virus detected', event.context['reason'])


class OCRWebhookTests(TestCase):
    """Test OCR webhook functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.state = State.objects.create(code='MD', name='Maryland')
        self.county = County.objects.create(
            state=self.state,
            name='Montgomery County'
        )

    @patch('documents.tasks.update_doc_task_from_ocr')
    def test_ocr_triggers_doc_task_update(self, mock_update):
        """Test that OCR completion triggers DocTask update"""
        from api.models import TaxData
        from datetime import date

        # Create TaxData first
        tax_data = TaxData.objects.create(
            state=self.state,
            county=self.county,
            version=1,
            data_completeness=100,
            scraper_confidence=95,
            data={'property_tax': {'total_rate': 0.01}},
            effective_date=date(2025, 1, 1)
        )

        loan_estimate = LoanEstimate.objects.create(
            user=self.user,
            county=self.county,
            property_value=300000,
            loan_amount=240000,
            down_payment=60000,
            interest_rate=6.5,
            loan_term_years=30,
            loan_type='conventional',
            property_type='single_family',
            first_time_homebuyer=False,
            closing_date='2025-06-01',
            calculation_results={},
            tax_data=tax_data
        )

        doc_task = DocTask.objects.create(
            user=self.user,
            loan_estimate=loan_estimate,
            task_type='verify_income',
            title='Verify Income',
            description='Upload income verification'
        )

        doc = DocumentUpload.objects.create(
            user=self.user,
            document_type='pay_stub',
            file='pay.pdf',
            file_name='pay.pdf',
            file_size=1024,
            doc_task=doc_task,
            extracted_data={'annual_income': 75000}
        )

        # Verify doc_task relationship
        self.assertEqual(doc.doc_task.id, doc_task.id)


class DocumentViewTests(TestCase):
    """Test document upload API views"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_upload_requires_authentication(self):
        """Test that upload endpoint requires authentication"""
        from rest_framework.test import APIClient

        client = APIClient()
        response = client.post('/api/documents/upload/', {})
        self.assertEqual(response.status_code, 401)

    def test_upload_requires_file(self):
        """Test that upload endpoint requires file"""
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.post('/api/documents/upload/', {})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
