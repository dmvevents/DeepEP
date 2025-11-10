QA Critique: Critical Gaps and Fixes

Architecture & Security Gaps:
- Missing encryption strategy for SSN in BorrowerProfile (current `ssn_encrypted` lacks key rotation/management)
  - Fix: Implement envelope encryption with AWS KMS or HashiCorp Vault
  - Add key rotation mechanism in backend/credit service

Data Validation Weaknesses:
- No explicit validation on critical fields like SSN, income sources
  - Add JSON Schema validation for IncomeProfile.w2_json, hourly_json
  - Implement strict regex/format checks on SSN before encryption
  - Create input sanitization middleware for all profile endpoints

Performance/Scalability Risks:
- ScenarioOutput lacks indexing strategy
  - Add composite index on (borrower_id, created_at)
  - Implement pagination/cursor-based retrieval for scenario history
  - Add caching layer for repeated DTI/scenario calculations

Compliance & Audit Concerns:
- AuditEvent lacks comprehensive tracking
  - Expand meta_json to include full request context
  - Add mandatory fields: ip_address, user_agent
  - Implement immutable append-only audit log

Authentication Gaps:
- No explicit role-based access control (RBAC) design
  - Create explicit RBAC matrix in platform/tenant-theming
  - Implement granular permission checks per endpoint
  - Add role inheritance/delegation mechanism

Recommended Immediate Actions:
1. Create comprehensive input validation library
2. Implement robust encryption service
3. Design RBAC middleware
4. Add comprehensive logging/error tracking