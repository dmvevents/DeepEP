"""
Document serializers
"""
from rest_framework import serializers
from .models import DocumentUpload


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for DocumentUpload model"""
    username = serializers.CharField(source='user.username', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = DocumentUpload
        fields = [
            'id', 'user', 'username', 'document_type', 'document_type_display',
            'file', 'file_name', 'file_size', 'status', 'status_display',
            'ocr_text', 'extracted_data', 'extraction_confidence',
            'error_message', 'uploaded_at', 'processed_at'
        ]
        read_only_fields = [
            'user', 'file_name', 'file_size', 'status',
            'ocr_text', 'extracted_data', 'extraction_confidence',
            'error_message', 'uploaded_at', 'processed_at'
        ]
