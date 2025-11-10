# Security & Compliance Documentation

## Overview

This document outlines the security and compliance measures implemented in the Real Estate Mortgage Calculator application to protect Personally Identifiable Information (PII) and ensure regulatory compliance with CFPB, FCRA, ECOA, and other financial regulations.

## Table of Contents

1. [PII Protection](#pii-protection)
2. [Field-Level Encryption](#field-level-encryption)
3. [Data Masking](#data-masking)
4. [Audit Logging](#audit-logging)
5. [Access Control (RBAC)](#access-control-rbac)
6. [Credit Reporting Compliance](#credit-reporting-compliance)
7. [Future Enhancements](#future-enhancements)

---

## PII Protection

### Non-Negotiable Requirements

✅ **PII encrypted at rest** - All sensitive PII is encrypted using AES-128
✅ **Field-level encryption** - SSN, account numbers, DOB encrypted individually
✅ **Masked in UI/logs** - SSN displayed as `***-**-1234` format
✅ **Principle of least privilege** - Scoped tokens, time-boxed file URLs
✅ **Immutable audit events** - All sensitive actions logged permanently

### PII Fields

The following fields are considered PII and are protected:

| Field | Model | Protection | Format |
|-------|-------|------------|--------|
| SSN | `CreditReport.ssn_encrypted` | AES-128 encryption | `***-**-1234` (masked) |
| Account Number | `Tradeline.account_number` | Stored as last 4 only | `****1234` |
| Date of Birth | Future enhancement | AES-128 encryption | TBD |

---

## Field-Level Encryption

### Implementation

Encryption is implemented using **Fernet symmetric encryption** (AES-128 in CBC mode with HMAC) via the `cryptography` library.

**Location:** `backend/api/encryption.py`

### Key Management

```python
# Configuration (settings.py)
FIELD_ENCRYPTION_KEY = env('FIELD_ENCRYPTION_KEY', default=SECRET_KEY[:32])
```

**⚠️ PRODUCTION WARNING:**
In production, the encryption key MUST be stored in a secure key management system:
- AWS Key Management Service (KMS)
- HashiCorp Vault
- Azure Key Vault
- Google Cloud KMS

**DO NOT** commit encryption keys to version control.

### Usage Example

```python
from api.encryption import encrypt_ssn, decrypt_ssn, mask_ssn

# Encrypt SSN for storage
encrypted = encrypt_ssn("123-45-6789")

# Decrypt SSN (admin only)
decrypted = decrypt_ssn(encrypted)  # Returns: "123456789"

# Mask SSN for display
masked = mask_ssn("123-45-6789")  # Returns: "***-**-6789"
```

### Model Integration

The `CreditReport` model provides helper methods for SSN handling:

```python
# Set SSN (encrypts automatically)
credit_report.set_ssn("123-45-6789")

# Get decrypted SSN (restricted access)
ssn = credit_report.get_ssn()

# Get masked SSN (safe for display)
masked = credit_report.get_ssn_masked()  # Returns: "***-**-6789"
```

---

## Data Masking

### SSN Masking

All SSN values are masked in:
- API responses (via serializers)
- Admin interface logs
- Audit event logs
- Error messages

**Format:** `***-**-XXXX` (last 4 digits only)

**Implementation:**
- `CreditReportSerializer.ssn_masked` - Read-only field that returns masked SSN
- `AuditEvent.ssn_last_four` - Only stores last 4 digits (never full SSN)

### Account Number Masking

Tradeline account numbers are stored as **last 4 digits only**:
- `Tradeline.account_number` - Stores `"1234"` not full account number
- Display format: `****1234`

---

## Audit Logging

### Immutable Audit Trail

All sensitive operations are logged to the `AuditEvent` model with:
- **Immutability** - No updates or deletes allowed (use database triggers in production)
- **Timestamp** - Indexed for fast queries
- **IP address** - Client IP captured
- **User agent** - Browser/client information
- **Context** - JSON field with operation-specific details

### Audit Event Types

| Event Type | Trigger | PII Logged |
|------------|---------|------------|
| `credit_consent` | User consents to credit pull | SSN last 4 |
| `credit_pull` | Credit report retrieved | SSN last 4 |
| `pii_access` | Sensitive data accessed | SSN last 4 |
| `document_view` | Document downloaded | N/A |
| `application_submit` | Loan application submitted | N/A |
| `application_approve` | Admin approves application | N/A |
| `application_reject` | Admin rejects application | N/A |

### Implementation

**Location:** `backend/api/views_credit.py`

```python
# Automatic audit logging for credit report access
class CreditReportViewSet(viewsets.ModelViewSet):
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Log audit event
        self._log_credit_access(
            event_type='credit_pull',
            credit_report=instance,
            context={'action': 'retrieve', 'full_report': True}
        )

        return Response(serializer.data)
```

### Querying Audit Logs

```python
# Get all credit pulls for a borrower
AuditEvent.objects.filter(
    event_type='credit_pull',
    ssn_last_four='6789'
).order_by('-timestamp')

# Get recent PII access events
AuditEvent.objects.filter(
    event_type='pii_access',
    timestamp__gte=timezone.now() - timedelta(days=7)
)
```

---

## Access Control (RBAC)

### Role-Based Access

| Role | Credit Reports | Tradelines | Audit Logs | Admin Actions |
|------|---------------|-----------|------------|---------------|
| **Borrower** | Own only | Own only | No access | No |
| **Loan Officer** | Assigned borrowers | Assigned borrowers | Limited | Limited |
| **Admin** | All | All | All | Yes |

### Implementation

```python
class CreditReportViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset  # All reports
        return self.queryset.filter(user=user)  # Own reports only
```

### Scoped Tokens

JWT tokens are scoped with:
- **Access token lifetime:** 60 minutes (configurable)
- **Refresh token lifetime:** 24 hours (configurable)
- **Token rotation:** Enabled (blacklist old tokens)

**Configuration:** `backend/config/settings.py`

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=1440),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

---

## Credit Reporting Compliance

### CFPB Credit Consent

✅ **Credit consent modal** - Required before credit pull
✅ **45-day rate-shopping guidance** - CFPB-compliant language included
✅ **Explicit user consent** - Logged in `AuditEvent`

**Implementation:** `frontend-react/src/components/Credit/CreditConsentModal.tsx`

### FCRA Compliance

✅ **Permissible purpose** - Credit pulled only for loan application
✅ **Adverse action notice** - Queue placeholder ready
✅ **Consumer rights** - FCRA disclosure provided

### ECOA Compliance

🚧 **Future-ready:** Adverse Action queue placeholder exists for ECOA compliance when underwriting decisions are made.

**Location:** `backend/api/models.py` - `AuditEvent` can be extended for adverse action tracking

---

## Future Enhancements

### Phase 2: Advanced PII Protection

- [ ] **Date of Birth encryption** - Add DOB field to `UserProfile` with encryption
- [ ] **Database-level encryption** - Implement PostgreSQL pgcrypto for additional layer
- [ ] **Key rotation** - Implement automated encryption key rotation
- [ ] **Hardware Security Module (HSM)** - Integrate HSM for key storage

### Phase 3: Advanced Compliance

- [ ] **GLBA Compliance** - Implement Gramm-Leach-Bliley Act safeguards
- [ ] **SOC 2 Type II** - Audit trail enhancements for certification
- [ ] **Data residency** - Multi-region compliance (GDPR, CCPA)
- [ ] **Adverse Action engine** - Automated ECOA-compliant notices

### Phase 4: Security Enhancements

- [ ] **Two-factor authentication (2FA)** - TOTP/SMS verification
- [ ] **IP whitelisting** - Restrict admin access by IP range
- [ ] **Session timeout** - Automatic logout after inactivity
- [ ] **Penetration testing** - Annual security audits

---

## Configuration Checklist

### Development Environment

- [x] Encryption key derived from `SECRET_KEY`
- [x] SSN masking enabled (`MASK_SSN_IN_LOGS=True`)
- [x] Audit logging enabled
- [x] Debug mode warning (never use in production)

### Production Environment

**Critical:**
- [ ] Set `FIELD_ENCRYPTION_KEY` in environment (from KMS/Vault)
- [ ] Set `DEBUG=False`
- [ ] Configure secure `SECRET_KEY` (never commit)
- [ ] Enable HTTPS (TLS 1.2+)
- [ ] Enable database backups (encrypted)
- [ ] Configure Sentry for error monitoring
- [ ] Review and rotate encryption keys quarterly
- [ ] Implement database-level audit log immutability (triggers)

**Optional:**
- [ ] Enable IP whitelisting for admin
- [ ] Configure WAF (Web Application Firewall)
- [ ] Enable rate limiting on auth endpoints
- [ ] Configure log aggregation (Datadog, Splunk)

---

## Contact & Support

For security concerns or compliance questions:
- **Email:** security@example.com (replace with actual contact)
- **Security Issues:** Report via GitHub Security Advisory (private)

**Last Updated:** 2025-11-09
**Version:** 1.0
**Reviewed By:** Compliance Team (Anton Alexander)
