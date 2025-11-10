"""
Virus scanning utilities for uploaded documents.
Supports ClamAV integration with fallback to basic validation.
"""
import os
import subprocess
from typing import Dict, Optional
from django.conf import settings
import logging

# Try to import python-magic, fall back to mimetypes if not available
try:
    import magic
    HAS_MAGIC = True
except (ImportError, OSError):
    import mimetypes
    HAS_MAGIC = False

logger = logging.getLogger(__name__)


class VirusScanner:
    """
    Virus scanner with ClamAV integration.

    Configuration:
    - ENABLE_VIRUS_SCAN (bool): Enable/disable scanning (default: True in prod)
    - CLAMAV_SOCKET_PATH (str): Path to ClamAV socket
    - ALLOWED_MIME_TYPES (list): Whitelist of allowed MIME types
    """

    def __init__(self):
        self.enabled = getattr(settings, 'ENABLE_VIRUS_SCAN', True)
        self.clamav_socket = getattr(settings, 'CLAMAV_SOCKET_PATH', '/var/run/clamav/clamd.ctl')
        self.allowed_mime_types = getattr(
            settings,
            'ALLOWED_DOCUMENT_MIME_TYPES',
            [
                'application/pdf',
                'image/jpeg',
                'image/png',
                'image/tiff',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/msword',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            ]
        )

    def scan_file(self, file_path: str) -> Dict:
        """
        Scan file for viruses and validate MIME type.

        Args:
            file_path: Absolute path to file

        Returns:
            Dict with:
                - safe (bool): True if file is safe
                - reason (str): Reason if not safe
                - scanned (bool): Whether virus scan was performed
                - mime_type (str): Detected MIME type
        """
        result = {
            'safe': True,
            'reason': '',
            'scanned': False,
            'mime_type': None
        }

        # 1. Validate MIME type
        mime_result = self._validate_mime_type(file_path)
        result['mime_type'] = mime_result['mime_type']

        if not mime_result['valid']:
            result['safe'] = False
            result['reason'] = mime_result['reason']
            logger.warning(f"File rejected due to MIME type: {file_path} ({mime_result['mime_type']})")
            return result

        # 2. Perform virus scan if enabled
        if self.enabled:
            scan_result = self._scan_with_clamav(file_path)
            result['scanned'] = scan_result['scanned']

            if not scan_result['safe']:
                result['safe'] = False
                result['reason'] = scan_result['reason']
                logger.error(f"Virus detected in file: {file_path} - {scan_result['reason']}")
                return result

        logger.info(f"File scan passed: {file_path} ({result['mime_type']})")
        return result

    def _validate_mime_type(self, file_path: str) -> Dict:
        """
        Validate file MIME type using python-magic or mimetypes fallback.

        Returns:
            Dict with 'valid' (bool), 'mime_type' (str), 'reason' (str)
        """
        try:
            if HAS_MAGIC:
                # Use python-magic if available
                mime = magic.Magic(mime=True)
                mime_type = mime.from_file(file_path)
            else:
                # Fallback to mimetypes based on file extension
                mime_type, _ = mimetypes.guess_type(file_path)
                if not mime_type:
                    mime_type = 'application/octet-stream'

            if mime_type in self.allowed_mime_types:
                return {
                    'valid': True,
                    'mime_type': mime_type,
                    'reason': ''
                }
            else:
                return {
                    'valid': False,
                    'mime_type': mime_type,
                    'reason': f'File type not allowed: {mime_type}'
                }

        except Exception as e:
            logger.error(f"MIME type detection failed for {file_path}: {str(e)}")
            return {
                'valid': False,
                'mime_type': 'unknown',
                'reason': f'MIME type detection failed: {str(e)}'
            }

    def _scan_with_clamav(self, file_path: str) -> Dict:
        """
        Scan file with ClamAV.

        Returns:
            Dict with 'safe' (bool), 'scanned' (bool), 'reason' (str)
        """
        # Check if ClamAV is available
        if not self._is_clamav_available():
            logger.warning("ClamAV not available, skipping virus scan")
            return {
                'safe': True,
                'scanned': False,
                'reason': 'ClamAV not available'
            }

        try:
            # Use clamdscan for faster scanning via daemon
            result = subprocess.run(
                ['clamdscan', '--no-summary', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Exit code 0 = clean, 1 = infected, 2 = error
            if result.returncode == 0:
                return {
                    'safe': True,
                    'scanned': True,
                    'reason': ''
                }
            elif result.returncode == 1:
                return {
                    'safe': False,
                    'scanned': True,
                    'reason': f'Virus detected: {result.stdout.strip()}'
                }
            else:
                logger.error(f"ClamAV scan error: {result.stderr}")
                return {
                    'safe': True,  # Fail open to avoid blocking on scan errors
                    'scanned': False,
                    'reason': 'Scan error (failed open)'
                }

        except subprocess.TimeoutExpired:
            logger.error(f"ClamAV scan timeout for {file_path}")
            return {
                'safe': True,
                'scanned': False,
                'reason': 'Scan timeout (failed open)'
            }
        except Exception as e:
            logger.error(f"ClamAV scan exception: {str(e)}", exc_info=True)
            return {
                'safe': True,
                'scanned': False,
                'reason': f'Scan exception (failed open): {str(e)}'
            }

    def _is_clamav_available(self) -> bool:
        """Check if ClamAV daemon is available."""
        try:
            result = subprocess.run(
                ['clamdscan', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False


# Singleton instance
virus_scanner = VirusScanner()
