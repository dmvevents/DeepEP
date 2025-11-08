"""
Document processing views
"""
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import DocumentUpload
from .tasks import process_document
from .serializers import DocumentUploadSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_document(request):
    """
    Upload a document for OCR processing

    POST /api/documents/upload/
    """
    if 'file' not in request.FILES:
        return Response({
            'error': 'No file provided'
        }, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['file']
    document_type = request.data.get('document_type', 'other')

    # Create document record
    document = DocumentUpload.objects.create(
        user=request.user,
        document_type=document_type,
        file=file,
        file_name=file.name,
        file_size=file.size,
        status='uploaded'
    )

    # Trigger OCR processing
    process_document.delay(document.id)

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
