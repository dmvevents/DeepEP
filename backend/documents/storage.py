"""
Storage abstraction for document uploads.
Supports local filesystem and AWS S3 via environment configuration.
"""
import os
from typing import BinaryIO, Optional
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)


class DocumentStorage:
    """
    Abstraction layer for document storage.
    Configurable via DOCUMENT_STORAGE_BACKEND env var.

    Backends:
    - 'local': Local filesystem (default for development)
    - 's3': AWS S3 (production)
    """

    def __init__(self):
        self.backend = getattr(settings, 'DOCUMENT_STORAGE_BACKEND', 'local')

    def save(self, file_path: str, content: BinaryIO) -> str:
        """
        Save file to storage backend.

        Args:
            file_path: Relative path for file (e.g., 'documents/2025/01/file.pdf')
            content: File content as binary IO

        Returns:
            Full path to saved file
        """
        try:
            if self.backend == 's3':
                return self._save_to_s3(file_path, content)
            else:
                return self._save_to_local(file_path, content)
        except Exception as e:
            logger.error(f"Storage save failed for {file_path}: {str(e)}", exc_info=True)
            raise

    def _save_to_local(self, file_path: str, content: BinaryIO) -> str:
        """Save to local filesystem using Django's default storage."""
        saved_path = default_storage.save(file_path, ContentFile(content.read()))
        logger.info(f"File saved to local storage: {saved_path}")
        return saved_path

    def _save_to_s3(self, file_path: str, content: BinaryIO) -> str:
        """
        Save to AWS S3.
        Requires django-storages and boto3 configured.
        """
        # Django-storages handles S3 via default_storage when configured
        saved_path = default_storage.save(file_path, ContentFile(content.read()))
        logger.info(f"File saved to S3: {saved_path}")
        return saved_path

    def delete(self, file_path: str) -> bool:
        """
        Delete file from storage backend.

        Args:
            file_path: Path to file to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            if default_storage.exists(file_path):
                default_storage.delete(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Storage delete failed for {file_path}: {str(e)}", exc_info=True)
            return False

    def exists(self, file_path: str) -> bool:
        """Check if file exists in storage."""
        return default_storage.exists(file_path)

    def get_url(self, file_path: str) -> Optional[str]:
        """
        Get public URL for file.

        Args:
            file_path: Path to file

        Returns:
            Public URL (S3 pre-signed) or local URL
        """
        try:
            return default_storage.url(file_path)
        except Exception as e:
            logger.error(f"Failed to get URL for {file_path}: {str(e)}")
            return None


# Singleton instance
document_storage = DocumentStorage()
