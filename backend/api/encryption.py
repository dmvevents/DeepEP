"""
PII Encryption and Masking Utilities

Provides field-level encryption for sensitive PII data (SSN, account numbers, DOB)
using Fernet symmetric encryption (AES-128 in CBC mode with HMAC).

Usage:
    encrypted_ssn = encrypt_ssn("123-45-6789")
    decrypted_ssn = decrypt_ssn(encrypted_ssn)
    masked = mask_ssn("123-45-6789")  # Returns: ***-**-6789
"""
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import hashlib


def _get_fernet():
    """
    Get Fernet instance with encryption key from settings.
    Key must be 32 url-safe base64-encoded bytes.
    """
    key = settings.FIELD_ENCRYPTION_KEY
    if isinstance(key, str):
        key = key.encode('utf-8')

    # Ensure key is proper length and format for Fernet
    key_hash = hashlib.sha256(key).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    return Fernet(fernet_key)


def encrypt_ssn(ssn: str) -> str:
    """
    Encrypt SSN for storage at rest.

    Args:
        ssn: SSN in any format (123-45-6789 or 123456789)

    Returns:
        Base64-encoded encrypted SSN string
    """
    if not ssn:
        return ''

    # Remove formatting
    clean_ssn = ''.join(filter(str.isdigit, ssn))

    fernet = _get_fernet()
    encrypted = fernet.encrypt(clean_ssn.encode('utf-8'))
    return encrypted.decode('utf-8')


def decrypt_ssn(encrypted_ssn: str) -> str:
    """
    Decrypt SSN from storage.

    Args:
        encrypted_ssn: Base64-encoded encrypted SSN

    Returns:
        Decrypted SSN (digits only, no formatting)
    """
    if not encrypted_ssn:
        return ''

    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted_ssn.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception:
        # Return empty string if decryption fails (corrupted data, wrong key, etc.)
        return ''


def mask_ssn(ssn: str) -> str:
    """
    Mask SSN to show only last 4 digits for display/logging.

    Args:
        ssn: SSN in any format (123-45-6789 or 123456789)

    Returns:
        Masked SSN in format ***-**-1234
    """
    if not ssn:
        return ''

    # Remove any non-digit characters
    clean_ssn = ''.join(filter(str.isdigit, ssn))

    # Return last 4 digits only, formatted
    if len(clean_ssn) >= 4:
        last_four = clean_ssn[-4:]
        return f'***-**-{last_four}'

    # If less than 4 digits, mask everything
    return '***-**-****'


def encrypt_account_number(account_number: str) -> str:
    """
    Encrypt account number for storage at rest.

    Args:
        account_number: Account number string

    Returns:
        Base64-encoded encrypted account number
    """
    if not account_number:
        return ''

    fernet = _get_fernet()
    encrypted = fernet.encrypt(account_number.encode('utf-8'))
    return encrypted.decode('utf-8')


def decrypt_account_number(encrypted_account: str) -> str:
    """
    Decrypt account number from storage.

    Args:
        encrypted_account: Base64-encoded encrypted account number

    Returns:
        Decrypted account number
    """
    if not encrypted_account:
        return ''

    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted_account.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception:
        return ''


def mask_account_number(account_number: str) -> str:
    """
    Mask account number to show only last 4 characters.

    Args:
        account_number: Account number string

    Returns:
        Masked account number (e.g., "****1234")
    """
    if not account_number:
        return ''

    if len(account_number) > 4:
        return '****' + account_number[-4:]

    return '****'


def encrypt_dob(dob: str) -> str:
    """
    Encrypt date of birth for storage at rest.

    Args:
        dob: Date of birth string (any format)

    Returns:
        Base64-encoded encrypted DOB
    """
    if not dob:
        return ''

    fernet = _get_fernet()
    encrypted = fernet.encrypt(dob.encode('utf-8'))
    return encrypted.decode('utf-8')


def decrypt_dob(encrypted_dob: str) -> str:
    """
    Decrypt date of birth from storage.

    Args:
        encrypted_dob: Base64-encoded encrypted DOB

    Returns:
        Decrypted DOB string
    """
    if not encrypted_dob:
        return ''

    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted_dob.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception:
        return ''
