"""
Document processing views
"""
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import DocumentUpload
from .tasks import scan_document, process_document
from .serializers import DocumentUploadSerializer
from .audit import log_document_event, extract_client_ip, extract_user_agent
from api.models import DocTask, LoanEstimate


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_document(request):
    """
    Upload a document for OCR processing.

    POST /api/documents/upload/

    Body params:
    - file (file): Document file
    - document_type (str): Type of document
    - doc_task_id (int, optional): Associated DocTask ID
    - loan_estimate_id (int, optional): Associated LoanEstimate ID
    """
    if 'file' not in request.FILES:
        return Response({
            'error': 'No file provided'
        }, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['file']
    document_type = request.data.get('document_type', 'other')
    doc_task_id = request.data.get('doc_task_id')
    loan_estimate_id = request.data.get('loan_estimate_id')

    # Validate file size
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size > max_size:
        return Response({
            'error': f'File too large. Maximum size is {max_size / (1024*1024)}MB'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Get optional associations
    doc_task = None
    loan_estimate = None

    if doc_task_id:
        try:
            doc_task = DocTask.objects.get(id=doc_task_id, user=request.user)
        except DocTask.DoesNotExist:
            return Response({
                'error': 'DocTask not found'
            }, status=status.HTTP_404_NOT_FOUND)

    if loan_estimate_id:
        try:
            loan_estimate = LoanEstimate.objects.get(id=loan_estimate_id, user=request.user)
        except LoanEstimate.DoesNotExist:
            return Response({
                'error': 'LoanEstimate not found'
            }, status=status.HTTP_404_NOT_FOUND)

    # Create document record
    document = DocumentUpload.objects.create(
        user=request.user,
        document_type=document_type,
        file=file,
        file_name=file.name,
        file_size=file.size,
        doc_task=doc_task,
        loan_estimate=loan_estimate,
        status='uploaded'
    )

    # Log audit event
    try:
        log_document_event(
            event_type='document_upload',
            user=request.user,
            document_id=document.id,
            loan_estimate=loan_estimate,
            context={
                'document_type': document_type,
                'file_name': file.name,
                'file_size': file.size,
                'doc_task_id': doc_task_id
            },
            ip_address=extract_client_ip(request),
            user_agent=extract_user_agent(request)
        )
    except Exception as e:
        # Don't fail the upload if audit logging fails
        pass

    # Trigger virus scan (which will trigger OCR if passed)
    scan_document.delay(document.id)

    serializer = DocumentUploadSerializer(document)

    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_document(request, document_id):
    """
    Get document details

    GET /api/documents/{document_id}/
    """
    try:
        document = DocumentUpload.objects.get(
            id=document_id,
            user=request.user
        )

        serializer = DocumentUploadSerializer(document)
        return Response(serializer.data)

    except DocumentUpload.DoesNotExist:
        return Response({
            'error': 'Document not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_extraction(request, document_id):
    """
    Manually trigger extraction for a document

    POST /api/documents/{document_id}/extract/
    """
    try:
        document = DocumentUpload.objects.get(
            id=document_id,
            user=request.user
        )

        if document.status == 'processing':
            return Response({
                'error': 'Document is already being processed'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Trigger processing
        process_document.delay(document.id)

        return Response({
            'message': 'Processing triggered',
            'document_id': document.id
        }, status=status.HTTP_202_ACCEPTED)

    except DocumentUpload.DoesNotExist:
        return Response({
            'error': 'Document not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_documents(request):
    """
    List user's documents

    GET /api/documents/
    """
    documents = DocumentUpload.objects.filter(user=request.user)

    # Filter by type if provided
    document_type = request.query_params.get('type')
    if document_type:
        documents = documents.filter(document_type=document_type)

    # Filter by status if provided
    status_filter = request.query_params.get('status')
    if status_filter:
        documents = documents.filter(status=status_filter)

    serializer = DocumentUploadSerializer(documents, many=True)

    return Response({
        'count': documents.count(),
        'results': serializer.data
    })
