# Admin System Documentation
## Real Estate Mortgage Calculator - Administrator Management

**Version**: 1.0
**Last Updated**: November 8, 2025
**Author**: Product & Engineering Team

---

## Table of Contents

1. [Overview](#overview)
2. [Role Hierarchy](#role-hierarchy)
3. [Permission Matrix](#permission-matrix)
4. [Super Admin Dashboard](#super-admin-dashboard)
5. [Admin Dashboard](#admin-dashboard)
6. [Security Features](#security-features)
7. [User Workflows](#user-workflows)
8. [API Integration](#api-integration)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Real Estate Mortgage Calculator implements a three-tier role-based access control (RBAC) system designed for financial institutions handling sensitive mortgage data. The system is built with security, auditability, and scalability in mind.

### Key Principles:
- **Least Privilege**: Users and admins only have access to what they need
- **Separation of Duties**: Super admins manage admins; admins manage applications
- **Audit Trail**: All sensitive data access is logged with timestamps and IP addresses
- **Data Protection**: RBAC enforced at both frontend and backend levels

---

## Role Hierarchy

### 1. **User (Customer)**
**Description**: Mortgage applicants who submit and track their own applications.

**Permissions**:
- Create mortgage applications
- View own applications
- Upload own documents (W-2, paystubs, tax returns)
- Edit applications in "draft" status
- Delete applications in "draft" status
- Update own profile

**Access Level**: Restricted to own data only

**Typical Users**:
- Emily Thompson (First-time homebuyer)
- Anyone submitting a mortgage pre-qualification

---

### 2. **Admin (Loan Officer)**
**Description**: Mortgage loan officers who review and process customer applications.

**Permissions**:
- View all mortgage applications
- Update application status (draft → submitted → under_review → approved/rejected/needs_correction)
- View customer documents (W-2s, paystubs, tax returns, bank statements)
- Add admin feedback to applications
- Generate reports on approval rates and processing times
- Update own profile

**Restricted From**:
- Cannot create/delete other admin accounts
- Cannot view audit logs
- Cannot change system settings
- Cannot access Super Admin dashboard

**Access Level**: Read/Write on customer applications, Read on customer profiles

**Typical Users**:
- Sarah Johnson (Loan Officer, MLO #123456)
- Michael Chen (Loan Officer, NMLS #876543)

**Profile Requirements**:
- Licensed Mortgage Loan Originator (MLO) number
- National Mortgage Licensing System (NMLS) ID
- Territory assignment (states/counties covered)
- 2FA enrollment recommended

---

### 3. **Super Admin (Master Administrator)**
**Description**: System administrators with full control over user management, security settings, and system configuration.

**Permissions**:
- **All Admin Permissions** +
- Create new admin accounts
- Edit existing admin accounts
- Activate/deactivate admin accounts
- Delete admin accounts (except other super admins)
- View security audit logs
- Configure system-wide security settings (2FA enforcement, session timeout, IP whitelist)
- View performance metrics for all admins
- Export compliance reports

**Access Level**: Full system access (except cannot delete own account)

**Typical Users**:
- IT Administrator
- Compliance Officer
- Chief Technology Officer

**Security Requirements**:
- **MANDATORY** 2FA enrollment
- Strong password policy (12+ characters, symbols, numbers)
- Session timeout: 30 minutes
- IP whitelist recommended for production

---

## Permission Matrix

| Resource | User | Admin | Super Admin |
|----------|------|-------|-------------|
| **Own Applications** | CRUD | Read | Read |
| **All Applications** | - | Read/Update | Read/Update/Delete |
| **Own Documents** | CRUD | Read | Read |
| **All Documents** | - | Read | Read/Delete |
| **Own Profile** | Read/Update | Read/Update | Read/Update |
| **Admin Accounts** | - | - | CRUD |
| **Audit Logs** | - | - | Read |
| **System Settings** | - | - | Read/Update |
| **User Accounts** | - | Read | Read/Update/Delete |

**Legend**: C = Create, R = Read, U = Update, D = Delete

---

## Super Admin Dashboard

### Access URL
```
https://yourdomain.com/super-admin
```

### Features

#### **Tab 1: Admin Management**

**Purpose**: Manage all administrator accounts in the system.

**Actions**:
1. **Add New Admin**
   - Click "Add New Admin" button
   - Fill in form:
     - First Name, Last Name
     - Email (must be unique)
     - Phone number
     - Role: `admin` or `super_admin`
     - License Number (MLO)
     - NMLS ID
     - Territory (comma-separated state codes: e.g., `MD, VA, DC`)
   - Submit to create account
   - Admin receives email with temporary password

2. **Edit Admin**
   - Click edit icon (pencil) on admin row
   - Modify details
   - Save changes
   - Admin notified of profile updates

3. **Activate/Deactivate Admin**
   - Click lock/unlock icon
   - Deactivated admins cannot log in but data is preserved
   - Use case: Admin on leave, suspended for investigation

4. **Delete Admin**
   - Click delete icon (trash)
   - Confirm deletion
   - Admin account permanently removed
   - **Warning**: Cannot be undone. Applications reviewed by this admin are preserved but attributed to "Deleted Admin"

**Table Columns**:
- **Admin**: Name, avatar, role badge (SUPER)
- **Contact**: Email, phone
- **License**: MLO number, NMLS ID
- **Territory**: State codes as chips
- **Performance**:
  - Total reviews
  - Approval rate (%)
  - Average review time (hours)
- **Security**: 2FA status (enabled/warning)
- **Status**: Active / Inactive
- **Actions**: View, Edit, Activate/Deactivate, Delete

---

#### **Tab 2: Audit Log**

**Purpose**: Track all administrator actions for compliance and security investigations.

**Log Entries Include**:
- **Timestamp**: Exact date/time of action
- **Admin**: Who performed the action
- **Action**: Type of action (viewed_application, updated_status, viewed_document, deleted_user, etc.)
- **Resource**: What was affected (application ID, document ID, user ID)
- **Details**: Human-readable description
- **Sensitive Data Flag**: Yes (PII/financial data) or No
- **IP Address**: Where the action originated

**Filters** (Future Enhancement):
- Date range
- Admin name
- Action type
- Sensitive data only

**Export Options** (Future Enhancement):
- Export to CSV
- Export to PDF
- Send to SIEM system

**Retention Policy**:
- Default: 1 year
- Configurable in Security Settings tab

**Compliance Use Cases**:
- CFPB audits
- Internal investigations
- Security incident response
- Performance reviews

---

#### **Tab 3: Security Settings**

**Purpose**: Configure system-wide security policies.

**Settings**:

1. **Two-Factor Authentication**
   - Enforce 2FA for all admins
   - Admins required to enroll within 7 days or account suspended
   - Supported methods: Google Authenticator, Authy, SMS backup

2. **Session Timeout**
   - Options: 15 min, 30 min, 1 hour, 2 hours
   - Recommended: 30 minutes for admins handling financial data
   - Idle sessions automatically logged out

3. **IP Whitelist**
   - Restrict admin access to specific IP addresses/ranges
   - Use case: Only allow access from office network
   - Format: CIDR notation (e.g., `192.168.1.0/24`)

4. **Audit Log Retention**
   - Options: 90 days, 180 days, 1 year, 2 years
   - Legal requirement: Check state regulations (typically 3-7 years for financial records)

---

### Statistics Cards (Top of Dashboard)

1. **Active Admins**
   - Count of admins with `is_active = true`
   - Click to filter table

2. **Total Reviews**
   - Sum of all applications reviewed by all admins
   - Includes approved, rejected, needs_correction

3. **Avg Approval Rate**
   - Average of all admins' approval rates
   - Formula: `(approved / (approved + rejected)) * 100`

4. **Missing 2FA**
   - Count of active admins without 2FA enabled
   - Color: Red if > 0, Green if 0
   - **Security Alert**: Displayed prominently if count > 0

---

## Admin Dashboard

### Access URL
```
https://yourdomain.com/admin
```

### Features

#### **Tab 1: Manage Borrowers**

**Purpose**: Review and manage mortgage applications from customers.

**Table Columns**:
- Loan Number
- Property Address
- Max Loan Amount
- DTI Ratio (Front-End / Back-End)
- Status (Draft, Submitted, Under Review, Needs Correction, Approved, Rejected)
- Actions: Review, Edit Status, Send Feedback

**Actions**:
1. **Review Application**
   - View full application details
   - See qualification results
   - Check DTI calculations
   - View uploaded documents

2. **Update Status**
   - Submitted → Under Review
   - Under Review → Approved / Rejected / Needs Correction
   - Needs Correction → Resubmitted → Under Review (loop)

3. **Send Feedback**
   - Text area for admin comments
   - Required for "Needs Correction" status
   - Customer notified via email

---

#### **Tab 2: View Documents**

**Purpose**: Access customer-uploaded documents for income verification.

**Document Types**:
- Paystubs (last 2 months)
- W-2 forms (last 2 years)
- Tax returns (1040, last 2 years)
- Bank statements (last 3 months)
- Employment verification letters

**Actions**:
- Preview document (in-app)
- Download document
- Flag for review (if discrepancies found)

**Security Note**: All document views are logged in audit log with "Sensitive Data: Yes" flag.

---

#### **Tab 3: DTI Warnings**

**Purpose**: Identify high-risk applications with debt-to-income ratios above thresholds.

**DTI Thresholds**:
- **Green** (Low Risk): Front-End < 28%, Back-End < 36%
- **Yellow** (Moderate Risk): Front-End 28-31%, Back-End 36-43%
- **Red** (High Risk): Front-End > 31%, Back-End > 43%

**Recommendations**:
1. **Increase Income**: Provide recent pay increase documentation
2. **Reduce Debts**: Pay off credit cards before applying
3. **Larger Down Payment**: Reduce loan amount to lower housing payment
4. **Consider Co-Borrower**: Add spouse or family member to increase income

---

## Security Features

### 1. Two-Factor Authentication (2FA)

**Why**: Financial data requires multi-layer security to prevent unauthorized access.

**How It Works**:
1. Admin logs in with username + password (first factor)
2. System sends 6-digit code via:
   - Google Authenticator app (recommended)
   - SMS text message (backup)
3. Admin enters code within 60 seconds
4. Code expires after use

**Enrollment Process**:
1. Navigate to Profile > Security > Enable 2FA
2. Scan QR code with Google Authenticator
3. Enter verification code to confirm
4. Save backup codes (for account recovery)

**Recovery**:
- If device lost: Use backup codes
- If backup codes lost: Super Admin can reset 2FA

---

### 2. Audit Logging

**What is Logged**:
- All admin actions (view, edit, delete)
- Sensitive data access (documents, SSN, bank account numbers)
- Failed login attempts
- Permission changes
- Admin account creation/deletion

**Format**:
```json
{
  "id": "log_abc123",
  "timestamp": "2025-11-08T14:30:22Z",
  "admin_id": "admin_xyz789",
  "admin_name": "Sarah Johnson",
  "action": "viewed_document",
  "resource_type": "document",
  "resource_id": "doc_456",
  "details": "Viewed W-2 form for user Emily Thompson",
  "ip_address": "192.168.1.10",
  "sensitive_data_accessed": true,
  "user_agent": "Mozilla/5.0..."
}
```

**Compliance**: Audit logs support CFPB, GLBA, and SOC 2 requirements.

---

### 3. Role-Based Access Control (RBAC)

**Implementation**:
- Frontend: React components conditionally render based on user role
- Backend: Django middleware checks permissions before API calls
- Database: Row-level security ensures admins only see assigned data

**Example**:
```typescript
// Frontend check
if (hasPermission(userRole, 'applications', 'delete')) {
  return <DeleteButton />;
}

// Backend check (Django)
if not request.user.has_perm('api.delete_application'):
    return HttpResponseForbidden()
```

---

### 4. Session Management

**Session Lifecycle**:
1. User logs in → JWT access token (15 min expiry)
2. Token stored in localStorage (encrypted)
3. Every API call includes `Authorization: Bearer <token>` header
4. Token expires → Refresh token used to get new access token
5. Refresh token expires (7 days) → User must log in again

**Automatic Logout**:
- Idle timeout (no activity for 30 minutes)
- Tab closed (session cleared)
- Logout button clicked

**Security Benefits**:
- Short-lived tokens reduce attack window
- Automatic logout prevents unauthorized access if device left unattended

---

## User Workflows

### Workflow 1: Super Admin Creates New Admin

**Actors**: Super Admin (Alice)

**Steps**:
1. Alice logs into `/super-admin`
2. Navigates to "Admin Management" tab
3. Clicks "Add New Admin" button
4. Fills form:
   - First Name: Sarah
   - Last Name: Johnson
   - Email: sarah.johnson@mortgageco.com
   - Phone: (555) 234-5678
   - Role: `admin`
   - License: MLO123456
   - NMLS ID: 987654
   - Territory: MD, VA, DC
5. Clicks "Create Admin"
6. System sends email to sarah.johnson@mortgageco.com with:
   - Welcome message
   - Temporary password
   - Link to reset password
   - Instructions to enable 2FA
7. Audit log records: `created_admin` action
8. Alice sees success message: "Admin created successfully!"

**Result**: Sarah can now log in and review applications in MD, VA, DC.

---

### Workflow 2: Admin Reviews Application

**Actors**: Admin (Sarah), Customer (Emily)

**Prerequisites**: Emily has submitted application ID `app_123`

**Steps**:
1. Sarah logs into `/admin`
2. Sees application `app_123` in "Submitted" status in table
3. Clicks "Review" button
4. System logs: `viewed_application` (Sensitive Data: Yes)
5. Sarah reviews:
   - Property: 123 Main St, Rockville, MD
   - Loan Amount: $400,000
   - DTI: Front-End 26%, Back-End 38%
   - Documents: 2 paystubs, 1 W-2, tax return ✓
6. Sarah clicks "View Documents" tab
7. System logs: `viewed_document` for each document
8. Sarah verifies income matches paystubs
9. Sarah updates status: Submitted → Under Review
10. System logs: `updated_status`
11. Emily receives email: "Your application is now under review"

**Next Steps**: Sarah continues review, eventually changes status to Approved or Needs Correction.

---

### Workflow 3: Admin Flags Application for Correction

**Actors**: Admin (Sarah), Customer (Emily)

**Steps**:
1. Sarah reviewing application `app_123`
2. Notices W-2 form is blurry and unreadable
3. Changes status: Under Review → Needs Correction
4. Required field appears: "Admin Feedback"
5. Sarah types: "Please upload a clearer copy of your 2024 W-2. The current image is too blurry to verify income."
6. Clicks "Send Feedback"
7. System logs: `updated_status` + `added_feedback`
8. Emily receives email with feedback
9. Emily logs into `/my-applications`
10. Sees application with red "Needs Correction" badge
11. Alert displays Sarah's feedback
12. Emily clicks "Make Corrections" button
13. Re-uploads clearer W-2
14. Changes status: Needs Correction → Resubmitted
15. Sarah notified: "Application app_123 has been resubmitted"

**Result**: Application cycle continues until approved or rejected.

---

### Workflow 4: Super Admin Investigates Security Incident

**Actors**: Super Admin (Alice), Admin (Michael)

**Scenario**: Compliance team reports suspicious activity on admin account.

**Steps**:
1. Alice logs into `/super-admin`
2. Navigates to "Audit Log" tab
3. Filters by:
   - Admin: Michael Chen
   - Date: Last 7 days
   - Sensitive Data: Yes
4. Reviews log entries:
   - **Nov 7, 2:00 AM**: `viewed_application` (app_789)
   - **Nov 7, 2:05 AM**: `viewed_document` (doc_123)
   - **Nov 7, 2:10 AM**: `viewed_document` (doc_456)
   - **IP Address**: 185.220.101.5 (Tor exit node - suspicious!)
5. Alice clicks on Michael's profile in Admin Management
6. Clicks "Deactivate" to immediately lock account
7. Alice contacts Michael: "Did you access applications at 2 AM from IP 185.220.101.5?"
8. Michael: "No, I was asleep. I've never seen that IP."
9. Alice determines account was compromised
10. Alice resets Michael's password
11. Requires Michael to re-enroll 2FA (old device compromised)
12. Alice enables IP whitelist for Michael (office network only)
13. Alice documents incident in compliance report

**Result**: Security breach contained, account secured, compliance documented.

---

## API Integration

### Backend Requirements

The frontend expects the following API endpoints:

#### **Authentication**
```
POST   /api/auth/login          # Returns access_token + refresh_token
POST   /api/auth/logout         # Blacklists refresh_token
POST   /api/auth/token/refresh  # Exchanges refresh_token for new access_token
POST   /api/auth/2fa/enroll     # Generates QR code for 2FA setup
POST   /api/auth/2fa/verify     # Verifies 6-digit 2FA code
```

#### **Admin Management (Super Admin Only)**
```
GET    /api/admins/             # List all admins
POST   /api/admins/             # Create new admin
GET    /api/admins/{id}/        # Get admin details
PATCH  /api/admins/{id}/        # Update admin
DELETE /api/admins/{id}/        # Delete admin
POST   /api/admins/{id}/toggle_active/  # Activate/deactivate
```

#### **Audit Logs (Super Admin Only)**
```
GET    /api/audit-logs/         # List all audit logs (with filters)
GET    /api/audit-logs/{id}/    # Get specific log entry
POST   /api/audit-logs/export/  # Export to CSV/PDF
```

#### **Applications (Admin + Super Admin)**
```
GET    /api/loan-estimates/           # List all applications
GET    /api/loan-estimates/{id}/      # Get application details
PATCH  /api/loan-estimates/{id}/      # Update application
POST   /api/loan-estimates/{id}/feedback/  # Add admin feedback
```

#### **Documents (Admin + Super Admin)**
```
GET    /api/documents/           # List documents for application
GET    /api/documents/{id}/view/ # View document (triggers audit log)
DELETE /api/documents/{id}/      # Delete document
```

---

### Request/Response Examples

#### Create Admin
```http
POST /api/admins/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "email": "sarah.johnson@mortgageco.com",
  "first_name": "Sarah",
  "last_name": "Johnson",
  "phone": "(555) 234-5678",
  "role": "admin",
  "license_number": "MLO123456",
  "nmls_id": "987654",
  "territory": ["MD", "VA", "DC"]
}

Response 201 Created:
{
  "id": "admin_xyz789",
  "email": "sarah.johnson@mortgageco.com",
  "first_name": "Sarah",
  "last_name": "Johnson",
  "role": "admin",
  "is_active": true,
  "two_factor_enabled": false,
  "created_at": "2025-11-08T14:30:22Z",
  "temporary_password": "Xy8#mP2$qL9@" // Send via email, do not log
}
```

#### Get Audit Logs
```http
GET /api/audit-logs/?admin_id=admin_xyz789&start_date=2025-11-01&end_date=2025-11-08
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Response 200 OK:
{
  "count": 127,
  "next": "/api/audit-logs/?page=2",
  "previous": null,
  "results": [
    {
      "id": "log_001",
      "timestamp": "2025-11-08T14:30:22Z",
      "admin_id": "admin_xyz789",
      "admin_name": "Sarah Johnson",
      "action": "viewed_application",
      "resource_type": "application",
      "resource_id": "app_123",
      "details": "Viewed application for 123 Main St, Rockville, MD",
      "ip_address": "192.168.1.10",
      "sensitive_data_accessed": true
    },
    // ... more logs
  ]
}
```

---

## Best Practices

### For Super Admins:

1. **Enable 2FA Immediately**
   - First login → Profile → Security → Enable 2FA
   - Store backup codes in secure location (password manager)

2. **Regularly Review Audit Logs**
   - Weekly: Check for unusual activity
   - Monthly: Generate compliance report

3. **Enforce 2FA for All Admins**
   - Use "Enforce 2FA" button in Security Settings
   - Set deadline: 7 days from notification

4. **Use Strong Passwords**
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, symbols
   - Use password manager (1Password, LastPass)

5. **Limit Super Admin Accounts**
   - Only 2-3 super admins needed
   - More = higher security risk

6. **Document Admin Changes**
   - Keep external log of who was created/deleted and why
   - Useful for compliance audits

---

### For Admins:

1. **Enable 2FA**
   - Even if not required, enable for extra security

2. **Log Out When Done**
   - Never leave session open on shared computer

3. **Review Applications Thoroughly**
   - Verify document authenticity
   - Check DTI calculations
   - Look for red flags (inconsistent income, suspicious documents)

4. **Provide Clear Feedback**
   - Specific: "Upload 2024 W-2" not "Need more docs"
   - Actionable: Tell customer exactly what to do

5. **Respect Customer Privacy**
   - Only access applications assigned to you
   - Don't share customer data outside system
   - Never email/text customer SSN or bank account numbers

---

### For Developers:

1. **Always Check Permissions**
   ```typescript
   if (!hasPermission(userRole, 'applications', 'delete')) {
     throw new Error('Forbidden');
   }
   ```

2. **Log Sensitive Actions**
   ```typescript
   await auditLog.create({
     admin_id: req.user.id,
     action: 'viewed_document',
     resource_id: documentId,
     sensitive_data_accessed: true,
     ip_address: req.ip
   });
   ```

3. **Use Environment Variables for Secrets**
   - Never commit API keys to Git
   - Use `.env.local` for local development
   - Use secrets manager in production (AWS Secrets Manager, etc.)

4. **Validate Input**
   - Sanitize all user input to prevent XSS, SQL injection
   - Use `validator` package for email, phone, etc.

5. **Test Permission Logic**
   - Unit tests for `hasPermission()` function
   - Integration tests for API endpoints
   - Test with different roles

---

## Troubleshooting

### Problem: Admin can't log in

**Symptoms**: "Invalid credentials" error despite correct password

**Causes**:
1. Account deactivated by super admin
2. Too many failed login attempts (account locked)
3. Password expired (if password rotation policy enabled)

**Solutions**:
1. Check if account is active: Super Admin → Admin Management → Look for "Inactive" badge
2. Super Admin can unlock account: Edit Admin → Reset failed login count
3. Reset password: Super Admin → Edit Admin → Generate new temporary password

---

### Problem: "Missing 2FA" warning won't go away

**Symptoms**: Security card shows admins missing 2FA, but all admins claim they enrolled

**Causes**:
1. Admin enrolled but didn't complete verification
2. Database flag not updated after enrollment
3. Admin using backup SMS method, not authenticator app (may not count as "enabled")

**Solutions**:
1. Ask admin to navigate to Profile → Security → Verify 2FA status
2. If "Pending", admin needs to scan QR code and enter verification code
3. Super Admin can check database: `SELECT id, email, two_factor_enabled FROM users WHERE role IN ('admin', 'super_admin');`

---

### Problem: Audit log not recording actions

**Symptoms**: Audit log tab is empty or missing recent entries

**Causes**:
1. Audit logging service crashed
2. Database write permissions issue
3. Logging disabled in environment variables

**Solutions**:
1. Check backend logs for errors: `grep "audit" /var/log/django/error.log`
2. Verify database connection: `python manage.py dbshell` then `SELECT COUNT(*) FROM audit_logs;`
3. Check `.env`: Ensure `ENABLE_AUDIT_LOGGING=true`

---

### Problem: Admin can see applications from wrong territory

**Symptoms**: Sarah (territory: MD, VA) sees applications from California

**Causes**:
1. Territory filtering not implemented in backend
2. Frontend filtering not working
3. Admin has multiple territories and CA was recently added

**Solutions**:
1. Verify backend query: `SELECT * FROM loan_estimates WHERE state IN (SELECT unnest(territory) FROM admins WHERE id=X);`
2. Check frontend filter logic in `AdminDashboard.tsx`
3. Super Admin → Edit Sarah → Verify territory list

---

## Appendix: Glossary

- **2FA**: Two-Factor Authentication - Security method requiring two forms of verification
- **CFPB**: Consumer Financial Protection Bureau - Federal agency regulating mortgages
- **DTI**: Debt-to-Income Ratio - Percentage of gross monthly income going to debt payments
- **GLBA**: Gramm-Leach-Bliley Act - Federal law requiring financial institutions to protect customer data
- **JWT**: JSON Web Token - Secure method of transmitting information between parties
- **MLO**: Mortgage Loan Originator - Licensed professional who helps consumers get mortgages
- **NMLS**: National Mortgage Licensing System - Registry of MLOs
- **RBAC**: Role-Based Access Control - Permission system based on user roles
- **SIEM**: Security Information and Event Management - Tool for monitoring security events
- **SOC 2**: Service Organization Control 2 - Audit for data security practices

---

## Contact & Support

**Technical Support**: support@mortgageco.com
**Security Issues**: security@mortgageco.com (PGP key: [link])
**Product Feedback**: product@mortgageco.com

**Emergency Contact** (Security Breach): +1 (555) 999-0000 (24/7)

---

**Document Control**
- Version: 1.0
- Classification: Internal Use Only
- Review Cycle: Quarterly
- Next Review: February 8, 2026
