Here's the comprehensive delivery plan based on the provided roadmap, data contracts, and brief:

### Delivery Plan Table

| Epic | Branches | Key Acceptance Criteria |
|------|----------|-------------------------|
| PHASE1: Harden Intake & Credit | - frontend/intake<br>- backend/credit<br>- ai/credit-normalization | - Complete purchase path to credit snapshot<br>- Debt confirm/dispute with auto doc tasks<br>- Mortgage check prompts<br>- PII encryption & access logging |
| PHASE2: Docs, OCR, Income Calc | - frontend/docs-portal<br>- backend/income<br>- ai/ocr | - OCR document upload with structured extraction<br>- Dynamic income calculation<br>- Complete doc task lifecycle |
| PHASE3: Pre-Approval & Scenarios | - frontend/scenario-desk<br>- backend/fee-pricing<br>- backend/dti | - 3 loan scenarios with rate/points<br>- PDF Loan Cost Estimate<br>- Realtor sharing with audit trail |
| PHASE4: Portal Polish & White-Label | - frontend/portal-polish<br>- platform/tenant-theming<br>- ops/observability | - Role-based access control<br>- Multi-tenant theming<br>- Comprehensive observability |

### JSON Backlog

```json
{
  "backlog": [
    {
      "id": "PHASE1-001",
      "title": "Secure Credit Intake Flow",
      "owner": "Credit Ops Persona",
      "acceptance": [
        "PII encrypted at rest",
        "SSN masked in all views",
        "Comprehensive access logging"
      ],
      "files_to_touch": [
        "src/intake/security.js",
        "src/credit/encryption.py",
        "db/migrations/credit_security.sql"
      ]
    },
    {
      "id": "PHASE2-002", 
      "title": "OCR Document Extraction",
      "owner": "Document Processing Persona",
      "acceptance": [
        "Support PDF/image upload",
        "Extract structured income data",
        "Validate extraction accuracy >90%"
      ],
      "files_to_touch": [
        "src/ocr/document_parser.py",
        "src/income/calculator.js",
        "tests/ocr_validation.spec.js"
      ]
    },
    {
      "id": "PHASE3-003",
      "title": "Loan Scenario Modeling",
      "owner": "Loan Officer Persona", 
      "acceptance": [
        "Generate 3 loan scenarios",
        "Calculate rate/points variations",
        "Produce watermarked PDF estimate"
      ],
      "files_to_touch": [
        "src/scenarios/generator.py",
        "src/pricing/calculator.js",
        "src/reporting/pdf_generator.py"
      ]
    },
    {
      "id": "PHASE4-004",
      "title": "Multi-Tenant Portal Theming",
      "owner": "Platform Engineering Persona",
      "acceptance": [
        "Dynamic tenant branding",
        "Role-based access controls",
        "Observability dashboards"
      ],
      "files_to_touch": [
        "src/portal/theming.js",
        "src/auth/rbac.py",
        "ops/monitoring/dashboards.yml"
      ]
    }
  ]
}
```

This plan provides a structured, actionable roadmap with clear epics, branches, acceptance criteria, and a detailed backlog of stories with ownership and technical context.