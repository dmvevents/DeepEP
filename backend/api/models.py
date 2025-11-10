"""
Core data models for mortgage calculator
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class State(models.Model):
    """US State model"""
    code = models.CharField(max_length=2, unique=True, help_text="Two-letter state code (e.g., 'MD')")
    name = models.CharField(max_length=100, help_text="Full state name")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class County(models.Model):
    """US County model"""
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='counties')
    name = models.CharField(max_length=100, help_text="County name")
    fips_code = models.CharField(max_length=5, unique=True, null=True, blank=True,
                                   help_text="5-digit FIPS code")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Counties"
        ordering = ['state__name', 'name']
        unique_together = ('state', 'name')
        indexes = [
            models.Index(fields=['state', 'name']),
            models.Index(fields=['fips_code']),
            models.Index(fields=['active']),
        ]

    def __str__(self):
        return f"{self.name}, {self.state.code}"


class TaxData(models.Model):
    """Scraped tax data for a state/county with versioning"""
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='tax_data')
    county = models.ForeignKey(County, on_delete=models.CASCADE, related_name='tax_data')

    # Versioning
    version = models.IntegerField(default=1)
    is_current = models.BooleanField(default=True, help_text="Is this the current version?")
    data_version = models.CharField(
        max_length=10,
        default="1.0",
        help_text="Schema version (e.g., '2.0' for enhanced schema)"
    )

    # Data completeness and confidence
    data_completeness = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of required fields populated (0-100)"
    )
    scraper_confidence = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="LLM confidence score (0-100)"
    )

    # Full tax data as JSON
    data = models.JSONField(
        help_text="Complete tax data structure including rates, fees, and calculations"
    )

    # Metadata
    effective_date = models.DateField(help_text="Date when these rates became effective")
    last_verified = models.DateTimeField(auto_now=True)
    sources = models.JSONField(default=list, help_text="List of source URLs")
    notes = models.TextField(blank=True, help_text="Additional notes or caveats")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Tax Data"
        ordering = ['-is_current', '-version', '-last_verified']
        unique_together = ('state', 'county', 'version')
        indexes = [
            models.Index(fields=['state', 'county', 'is_current']),
            models.Index(fields=['last_verified']),
            models.Index(fields=['data_completeness']),
            models.Index(fields=['effective_date']),
        ]

    def __str__(self):
        return f"{self.county.name}, {self.state.code} - v{self.version} ({'current' if self.is_current else 'historical'})"

    def save(self, *args, **kwargs):
        # If this is being set as current, mark all others as not current
        if self.is_current:
            TaxData.objects.filter(
                state=self.state,
                county=self.county,
                is_current=True
            ).exclude(id=self.id).update(is_current=False)
        super().save(*args, **kwargs)

    @property
    def is_stale(self):
        """Check if data is older than configured expiry days"""
        from django.conf import settings
        from datetime import timedelta

        expiry_days = getattr(settings, 'SCRAPER_CACHE_EXPIRY_DAYS', 30)
        expiry_date = timezone.now() - timedelta(days=expiry_days)
        return self.last_verified < expiry_date


class Municipality(models.Model):
    """Municipality within a county (for overlapping tax jurisdictions)"""
    county = models.ForeignKey(County, on_delete=models.CASCADE, related_name='municipalities')
    name = models.CharField(max_length=100)
    millage_rate = models.DecimalField(
        max_digits=8,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="Additional municipal tax rate"
    )
    zip_codes = models.JSONField(default=list, help_text="List of zip codes in this municipality")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Municipalities"
        ordering = ['county', 'name']
        unique_together = ('county', 'name')

    def __str__(self):
        return f"{self.name}, {self.county.name}"


class ScraperLog(models.Model):
    """Audit trail for all scraping operations"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    ]

    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='scraper_logs')
    county = models.ForeignKey(County, on_delete=models.CASCADE, related_name='scraper_logs')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Performance metrics
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True, help_text="Time in seconds")

    # Results
    data_completeness = models.IntegerField(null=True, blank=True)
    confidence_score = models.IntegerField(null=True, blank=True)
    sources_found = models.IntegerField(default=0)

    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)

    # LLM usage
    llm_provider = models.CharField(max_length=50, blank=True)
    llm_model = models.CharField(max_length=100, blank=True)
    tokens_used = models.IntegerField(null=True, blank=True)

    # Trigger information
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who triggered this scrape (if manual)"
    )
    trigger_type = models.CharField(
        max_length=20,
        choices=[
            ('manual', 'Manual'),
            ('api', 'API Request'),
            ('scheduled', 'Scheduled'),
            ('stale_data', 'Stale Data Refresh'),
        ],
        default='api'
    )

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['state', 'county', '-started_at']),
            models.Index(fields=['status']),
            models.Index(fields=['-started_at']),
        ]

    def __str__(self):
        return f"{self.county.name}, {self.state.code} - {self.status} ({self.started_at})"


class UserProfile(models.Model):
    """Extended user profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # User preferences
    default_state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    default_county = models.ForeignKey(County, on_delete=models.SET_NULL, null=True, blank=True)

    # Saved financial information (encrypted in production)
    annual_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    credit_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(300), MaxValueValidator(850)]
    )

    # Mortgage status tracking (Phase 1: Intake & Credit)
    mortgage_statuses = models.JSONField(
        default=list,
        blank=True,
        help_text="List of mortgage status objects tracking forbearance, modifications, transfers, and foreclosures"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile: {self.user.username}"


class LoanEstimate(models.Model):
    """Saved loan estimate calculations"""
    LOAN_TYPE_CHOICES = [
        ('conventional', 'Conventional'),
        ('fha', 'FHA'),
        ('va', 'VA'),
        ('usda', 'USDA'),
    ]

    PROPERTY_TYPE_CHOICES = [
        ('single_family', 'Single Family'),
        ('condo', 'Condominium'),
        ('townhouse', 'Townhouse'),
        ('multi_family', 'Multi-Family'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('needs_correction', 'Needs Correction'),
        ('resubmitted', 'Resubmitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_estimates')

    # Property information
    property_address = models.TextField(blank=True)
    county = models.ForeignKey(County, on_delete=models.PROTECT, related_name='loan_estimates')
    property_value = models.DecimalField(max_digits=12, decimal_places=2)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)

    # Loan details
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    down_payment = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=3, help_text="Annual interest rate (e.g., 6.5)")
    loan_term_years = models.IntegerField(default=30)
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPE_CHOICES)

    # Buyer information
    first_time_homebuyer = models.BooleanField(default=False)
    closing_date = models.DateField()

    # Calculated results (stored as JSON)
    calculation_results = models.JSONField(
        help_text="Complete calculation breakdown including all sections"
    )

    # Tax data version used
    tax_data = models.ForeignKey(
        TaxData,
        on_delete=models.PROTECT,
        related_name='loan_estimates',
        help_text="Version of tax data used in this calculation"
    )

    # Application status and workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Current application status"
    )
    submitted_at = models.DateTimeField(null=True, blank=True, help_text="When user submitted application")
    reviewed_at = models.DateTimeField(null=True, blank=True, help_text="When admin reviewed application")
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_loan_estimates',
        help_text="Admin who reviewed this application"
    )
    admin_feedback = models.TextField(
        blank=True,
        help_text="Admin feedback for corrections or rejection reason"
    )
    correction_count = models.IntegerField(
        default=0,
        help_text="Number of times application was sent back for corrections"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_saved = models.BooleanField(default=False, help_text="User chose to save this estimate")
    name = models.CharField(max_length=200, blank=True, help_text="User-provided name for this estimate")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['county']),
            models.Index(fields=['is_saved']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['submitted_at']),
        ]

    def __str__(self):
        return f"Loan Estimate for {self.user.username} - {self.property_value} ({self.created_at.date()})"

    @property
    def loan_to_value(self):
        """Calculate LTV ratio"""
        return (self.loan_amount / self.property_value) * 100

    @property
    def monthly_payment(self):
        """Extract monthly payment from calculation results"""
        return self.calculation_results.get('section_b', {}).get('estimated_total_monthly_payment', 0)


class AuditEvent(models.Model):
    """
    Audit trail for sensitive operations (credit consent, PII access, etc.)
    """
    EVENT_TYPES = [
        ('credit_consent', 'Credit Consent Given'),
        ('credit_pull', 'Credit Report Pulled'),
        ('pii_access', 'PII Data Accessed'),
        ('document_view', 'Document Viewed'),
        ('document_upload', 'Document Uploaded'),
        ('document_scan', 'Document Virus Scanned'),
        ('document_ocr', 'Document OCR Processed'),
        ('document_rejected', 'Document Rejected'),
        ('application_submit', 'Application Submitted'),
        ('application_approve', 'Application Approved'),
        ('application_reject', 'Application Rejected'),
        ('preapproval_create', 'Pre-Approval Created'),
        ('preapproval_submit', 'Pre-Approval Submitted'),
        ('preapproval_approve', 'Pre-Approval Approved'),
        ('preapproval_deny', 'Pre-Approval Denied'),
        ('preapproval_letter_generate', 'Pre-Approval Letter Generated'),
        ('preapproval_letter_publish', 'Pre-Approval Letter Published'),
    ]

    # Event metadata
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # User information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_events',
        help_text="User who triggered the event"
    )
    borrower_name = models.CharField(max_length=200, blank=True)

    # PII protection: Only store last 4 digits of SSN
    ssn_last_four = models.CharField(
        max_length=4,
        blank=True,
        help_text="Last 4 digits of SSN (masked for security)"
    )

    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Related objects
    loan_estimate = models.ForeignKey(
        LoanEstimate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_events'
    )

    # Additional context (JSON for flexibility)
    context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context data for the event"
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['ssn_last_four', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.borrower_name} ({self.timestamp})"

    @staticmethod
    def mask_ssn(ssn: str) -> str:
        """
        Mask SSN to only last 4 digits for logging
        Input: '123456789' or '123-45-6789'
        Output: '6789'
        """
        if not ssn:
            return ''
        # Remove any non-digit characters
        clean_ssn = ''.join(filter(str.isdigit, ssn))
        # Return last 4 digits only
        return clean_ssn[-4:] if len(clean_ssn) >= 4 else clean_ssn


class CreditReport(models.Model):
    """
    Stores credit report data pulled for a borrower.
    Phase 1: Basic credit snapshot with scores, tradelines, and inquiries.
    """
    BUREAU_CHOICES = [
        ('equifax', 'Equifax'),
        ('experian', 'Experian'),
        ('transunion', 'TransUnion'),
        ('merged', 'Merged Report'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Pull'),
        ('pulled', 'Successfully Pulled'),
        ('error', 'Error'),
        ('expired', 'Expired'),
    ]

    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='credit_reports',
        help_text="Borrower whose credit was pulled"
    )
    loan_estimate = models.ForeignKey(
        LoanEstimate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_reports',
        help_text="Associated loan application"
    )

    # PII: Encrypted SSN (field-level encryption at rest)
    ssn_encrypted = models.TextField(
        blank=True,
        help_text="Encrypted SSN for borrower identity verification (AES-128)"
    )

    # Credit Bureau Information
    bureau = models.CharField(max_length=20, choices=BUREAU_CHOICES, default='merged')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Credit Scores (all three bureaus for merged reports)
    equifax_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(300), MaxValueValidator(850)]
    )
    experian_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(300), MaxValueValidator(850)]
    )
    transunion_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(300), MaxValueValidator(850)]
    )

    # Report Metadata
    report_date = models.DateTimeField(auto_now_add=True)
    report_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="External credit bureau reference ID"
    )

    # Full report data (JSON)
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw credit report data from bureau API"
    )

    # Summary Statistics
    total_tradelines = models.IntegerField(default=0)
    total_inquiries = models.IntegerField(default=0)
    total_monthly_debt = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Sum of all monthly debt payments"
    )

    # Error handling
    error_message = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Credit reports expire after 120 days"
    )

    class Meta:
        ordering = ['-report_date']
        indexes = [
            models.Index(fields=['user', '-report_date']),
            models.Index(fields=['loan_estimate']),
            models.Index(fields=['status']),
            models.Index(fields=['-report_date']),
        ]

    def __str__(self):
        return f"Credit Report for {self.user.username} - {self.report_date.date()}"

    @property
    def middle_score(self):
        """Return the middle (representative) credit score from three bureaus"""
        scores = [s for s in [self.equifax_score, self.experian_score, self.transunion_score] if s]
        if not scores:
            return None
        if len(scores) == 1:
            return scores[0]
        return sorted(scores)[len(scores) // 2]

    @property
    def is_expired(self):
        """Check if credit report has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def set_ssn(self, ssn: str):
        """
        Encrypt and store SSN.
        Args:
            ssn: SSN in any format (123-45-6789 or 123456789)
        """
        from .encryption import encrypt_ssn
        self.ssn_encrypted = encrypt_ssn(ssn)

    def get_ssn(self) -> str:
        """
        Decrypt and return SSN (digits only).
        Returns:
            Decrypted SSN or empty string
        """
        from .encryption import decrypt_ssn
        return decrypt_ssn(self.ssn_encrypted)

    def get_ssn_masked(self) -> str:
        """
        Get masked SSN for display (***-**-1234).
        Returns:
            Masked SSN string
        """
        from .encryption import decrypt_ssn, mask_ssn
        ssn = decrypt_ssn(self.ssn_encrypted)
        return mask_ssn(ssn)


class Tradeline(models.Model):
    """
    Individual credit tradeline (debt account) from credit report.
    Phase 1: Basic tradeline info with borrower confirmation workflow.
    Enhanced: Normalized fields for lates/DLA, inquiries, remarks, special flags.
    """
    ACCOUNT_TYPE_CHOICES = [
        ('mortgage', 'Mortgage'),
        ('auto', 'Auto Loan'),
        ('student', 'Student Loan'),
        ('credit_card', 'Credit Card'),
        ('personal', 'Personal Loan'),
        ('installment', 'Installment Loan'),
        ('collection', 'Collection Account'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('paid', 'Paid Off'),
        ('charge_off', 'Charge Off'),
        ('collection', 'In Collection'),
    ]

    CONFIRMATION_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('confirmed', 'Confirmed'),
        ('disputed', 'Disputed'),
    ]

    # Relationships
    credit_report = models.ForeignKey(
        CreditReport,
        on_delete=models.CASCADE,
        related_name='tradelines'
    )

    # Account Information
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    creditor_name = models.CharField(max_length=200)
    account_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Last 4 digits only for security"
    )

    # Balance and Payment Information
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="For revolving accounts"
    )

    # Account Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    opened_date = models.DateField(null=True, blank=True)
    last_payment_date = models.DateField(null=True, blank=True)
    days_past_due = models.IntegerField(default=0)

    # === Enhanced: Days Late Activity (DLA) Tracking ===
    lates_30_count_24mo = models.IntegerField(
        default=0,
        help_text="Count of 30+ day late payments in last 24 months"
    )
    lates_60_count_24mo = models.IntegerField(
        default=0,
        help_text="Count of 60+ day late payments in last 24 months"
    )
    lates_90_count_24mo = models.IntegerField(
        default=0,
        help_text="Count of 90+ day late payments in last 24 months"
    )
    lates_30_count_36mo = models.IntegerField(
        default=0,
        help_text="Count of 30+ day late payments in last 36 months"
    )
    lates_60_count_36mo = models.IntegerField(
        default=0,
        help_text="Count of 60+ day late payments in last 36 months"
    )
    lates_90_count_36mo = models.IntegerField(
        default=0,
        help_text="Count of 90+ day late payments in last 36 months"
    )

    # === Enhanced: Special Account Flags ===
    is_deferred = models.BooleanField(
        default=False,
        help_text="Account is in deferment (common for student loans)"
    )
    is_ibr = models.BooleanField(
        default=False,
        help_text="Income-Based Repayment plan (student loans)"
    )
    is_cosigned = models.BooleanField(
        default=False,
        help_text="Account has a co-signer"
    )
    is_disputed = models.BooleanField(
        default=False,
        help_text="Borrower is disputing this tradeline with bureau"
    )
    has_less_than_10_payments = models.BooleanField(
        default=False,
        help_text="Account has fewer than 10 reported payments (new account)"
    )

    # === Enhanced: Payment History Metadata ===
    payment_count = models.IntegerField(
        default=0,
        help_text="Total number of payments reported"
    )
    months_reviewed = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of months of payment history available"
    )

    # === Enhanced: Remarks and Notes ===
    remarks = models.TextField(
        blank=True,
        help_text="Creditor remarks or bureau notes (e.g., 'Account closed by consumer')"
    )

    # Borrower Confirmation Workflow
    confirmation_status = models.CharField(
        max_length=20,
        choices=CONFIRMATION_STATUS_CHOICES,
        default='pending'
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    dispute_reason = models.TextField(blank=True)

    # Raw data from credit bureau
    raw_data = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['account_type', '-current_balance']
        indexes = [
            models.Index(fields=['credit_report', 'confirmation_status']),
            models.Index(fields=['account_type']),
            models.Index(fields=['confirmation_status']),
            models.Index(fields=['is_deferred', 'is_ibr']),
            models.Index(fields=['has_less_than_10_payments']),
        ]

    def __str__(self):
        return f"{self.get_account_type_display()} - {self.creditor_name} (${self.current_balance})"

    @property
    def needs_confirmation(self):
        """Check if tradeline requires borrower confirmation"""
        return self.confirmation_status == 'pending'

    @property
    def has_recent_lates(self):
        """Check if account has any late payments in last 24 months"""
        return (
            self.lates_30_count_24mo > 0 or
            self.lates_60_count_24mo > 0 or
            self.lates_90_count_36mo > 0
        )

    @property
    def total_lates_24mo(self):
        """Total count of all late payments in last 24 months"""
        return (
            self.lates_30_count_24mo +
            self.lates_60_count_24mo +
            self.lates_90_count_24mo
        )


class DocTask(models.Model):
    """
    Document task for borrower action (upload supporting docs, provide explanation, etc.)
    Created when borrower disputes/confirms tradelines or when additional verification needed.
    """
    TASK_TYPE_CHOICES = [
        ('dispute_tradeline', 'Dispute Tradeline'),
        ('verify_tradeline', 'Verify Tradeline'),
        ('upload_document', 'Upload Supporting Document'),
        ('provide_explanation', 'Provide Explanation'),
        ('verify_income', 'Verify Income'),
        ('verify_assets', 'Verify Assets'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='doc_tasks'
    )
    loan_estimate = models.ForeignKey(
        LoanEstimate,
        on_delete=models.CASCADE,
        related_name='doc_tasks',
        null=True,
        blank=True
    )
    tradeline = models.ForeignKey(
        Tradeline,
        on_delete=models.CASCADE,
        related_name='doc_tasks',
        null=True,
        blank=True,
        help_text="Associated tradeline if task is debt-related"
    )

    # Task Details
    task_type = models.CharField(max_length=30, choices=TASK_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Instructions for borrower")

    # Response from Borrower
    borrower_notes = models.TextField(blank=True)
    uploaded_documents = models.JSONField(
        default=list,
        blank=True,
        help_text="List of document IDs uploaded for this task"
    )

    # Admin Review
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_doc_tasks'
    )
    admin_notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['status', 'due_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['loan_estimate', 'status']),
            models.Index(fields=['tradeline']),
            models.Index(fields=['status', 'due_date']),
        ]

    def __str__(self):
        return f"{self.get_task_type_display()} - {self.user.username} ({self.status})"

    @property
    def is_overdue(self):
        """Check if task is past due date"""
        if not self.due_date or self.status in ['completed', 'cancelled']:
            return False
        return timezone.now().date() > self.due_date


class PreApproval(models.Model):
    """
    Pre-approval letter data for borrowers.
    Stores borrower financials, property details, and approval parameters.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('expired', 'Expired'),
    ]

    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pre_approvals',
        help_text="Loan officer or admin who created this pre-approval"
    )
    loan_estimate = models.ForeignKey(
        LoanEstimate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pre_approvals',
        help_text="Optional reference to existing loan estimate"
    )

    # Borrower Information
    borrower_name = models.CharField(max_length=200)
    co_borrower_name = models.CharField(max_length=200, blank=True)
    borrower_email = models.EmailField(blank=True)
    borrower_phone = models.CharField(max_length=20, blank=True)

    # Financial Information
    annual_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    monthly_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_assets = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_liabilities = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    credit_score_estimate = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(850)],
        help_text="Estimated credit score"
    )

    # DTI Calculations
    front_end_dti = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Front-end debt-to-income ratio"
    )
    back_end_dti = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Back-end debt-to-income ratio"
    )

    # Property Details
    property_address = models.TextField(blank=True)
    property_value_estimate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    down_payment_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    loan_type = models.CharField(
        max_length=20,
        choices=[
            ('conventional', 'Conventional'),
            ('fha', 'FHA'),
            ('va', 'VA'),
            ('usda', 'USDA'),
        ],
        default='conventional'
    )

    # Approval Parameters
    max_loan_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Maximum approved loan amount"
    )
    max_purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Maximum approved purchase price"
    )
    estimated_rate = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Estimated interest rate"
    )
    expiration_date = models.DateField(
        help_text="Date when pre-approval expires"
    )

    # Status and Workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # Letter Information
    letter_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the official letter was generated"
    )
    letter_published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the letter was published/sent"
    )
    letter_pdf_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to generated PDF letter"
    )

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_pre_approvals',
        help_text="Admin who approved this pre-approval"
    )

    # Additional Notes
    internal_notes = models.TextField(
        blank=True,
        help_text="Internal notes (not shown on letter)"
    )
    conditions = models.TextField(
        blank=True,
        help_text="Special conditions or requirements"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['expiration_date']),
            models.Index(fields=['borrower_email']),
        ]

    def __str__(self):
        return f"Pre-Approval: {self.borrower_name} - ${self.max_loan_amount} ({self.status})"

    @property
    def is_expired(self):
        """Check if pre-approval has expired"""
        if self.status == 'expired':
            return True
        if self.expiration_date:
            return timezone.now().date() > self.expiration_date
        return False

    @property
    def down_payment_percentage(self):
        """Calculate down payment percentage"""
        if self.property_value_estimate > 0:
            return (self.down_payment_amount / self.property_value_estimate) * 100
        return 0

    @property
    def loan_to_value(self):
        """Calculate LTV ratio"""
        if self.property_value_estimate > 0:
            loan_amount = self.property_value_estimate - self.down_payment_amount
            return (loan_amount / self.property_value_estimate) * 100
        return 0


class PricingScenario(models.Model):
    """
    Pricing scenario for Scenario Desk.
    Stores loan parameters and pricing options from investor bot/API.
    """
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pricing_scenarios',
        help_text="User who created this scenario"
    )
    loan_estimate = models.ForeignKey(
        LoanEstimate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pricing_scenarios',
        help_text="Optional reference to loan estimate"
    )

    # Loan Parameters (for pricing request)
    loan_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    property_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    credit_score = models.IntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(850)]
    )
    loan_type = models.CharField(
        max_length=20,
        choices=[
            ('conventional', 'Conventional'),
            ('fha', 'FHA'),
            ('va', 'VA'),
            ('usda', 'USDA'),
        ],
        default='conventional'
    )
    occupancy = models.CharField(
        max_length=20,
        choices=[
            ('primary', 'Primary Residence'),
            ('secondary', 'Secondary Home'),
            ('investment', 'Investment Property'),
        ],
        default='primary'
    )
    property_type = models.CharField(
        max_length=20,
        choices=[
            ('single_family', 'Single Family'),
            ('condo', 'Condominium'),
            ('townhouse', 'Townhouse'),
            ('multi_family', 'Multi-Family'),
        ],
        default='single_family'
    )
    loan_term_months = models.IntegerField(
        default=360,
        validators=[MinValueValidator(1)],
        help_text="Loan term in months (360 = 30 years, 180 = 15 years)"
    )
    loan_purpose = models.CharField(
        max_length=20,
        choices=[
            ('purchase', 'Purchase'),
            ('refinance', 'Refinance'),
            ('cash_out', 'Cash-Out Refinance'),
        ],
        default='purchase'
    )
    documentation_type = models.CharField(
        max_length=20,
        choices=[
            ('full_doc', 'Full Documentation'),
            ('alt_doc', 'Alternative Documentation'),
            ('no_doc', 'No Documentation'),
        ],
        default='full_doc'
    )

    # Optional location fields
    state = models.CharField(max_length=2, blank=True)
    county = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    debt_to_income_ratio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Pricing Response (stored as JSON)
    pricing_options = models.JSONField(
        default=list,
        help_text="List of pricing options from investor API"
    )
    selected_option_index = models.IntegerField(
        null=True,
        blank=True,
        help_text="Index of selected pricing option in pricing_options array"
    )

    # Pricing Metadata
    pricing_provider = models.CharField(
        max_length=100,
        default='MockInvestor',
        help_text="Name of pricing adapter/provider"
    )
    pricing_timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When pricing was retrieved"
    )
    pricing_request_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="External pricing request ID for audit trail"
    )
    execution_time_ms = models.IntegerField(
        default=0,
        help_text="Pricing API execution time in milliseconds"
    )

    # Scenario Metadata
    name = models.CharField(
        max_length=200,
        blank=True,
        help_text="User-provided scenario name"
    )
    notes = models.TextField(
        blank=True,
        help_text="User notes about this scenario"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['loan_estimate']),
            models.Index(fields=['pricing_provider', '-created_at']),
            models.Index(fields=['-pricing_timestamp']),
        ]

    def __str__(self):
        return f"Pricing Scenario: {self.name or self.loan_type} - ${self.loan_amount} ({self.created_at.date()})"

    @property
    def ltv_ratio(self):
        """Calculate loan-to-value ratio"""
        if self.property_value > 0:
            return (self.loan_amount / self.property_value * 100)
        return 0

    @property
    def selected_option(self):
        """Get selected pricing option"""
        if self.selected_option_index is not None and self.pricing_options:
            if 0 <= self.selected_option_index < len(self.pricing_options):
                return self.pricing_options[self.selected_option_index]
        return None

    def get_best_rate_option(self):
        """Get pricing option with lowest rate"""
        if not self.pricing_options:
            return None
        return min(self.pricing_options, key=lambda x: x.get('rate', 999))

    def get_zero_cost_option(self):
        """Get pricing option closest to zero net cost"""
        if not self.pricing_options:
            return None
        return min(
            self.pricing_options,
            key=lambda x: abs(x.get('points', 0) - x.get('credit', 0))
        )


class PricingAuditLog(models.Model):
    """
    Audit log for pricing requests.
    Tracks all pricing API calls for compliance and debugging.
    """
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pricing_audit_logs'
    )
    pricing_scenario = models.ForeignKey(
        PricingScenario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )

    # Request details
    pricing_provider = models.CharField(max_length=100)
    request_parameters = models.JSONField(
        help_text="Full request parameters sent to pricing API"
    )
    response_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Full response from pricing API"
    )

    # Execution metadata
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    execution_time_ms = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('error', 'Error'),
            ('timeout', 'Timeout'),
            ('validation_error', 'Validation Error'),
        ],
        default='success'
    )
    error_message = models.TextField(blank=True)

    # Request context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['pricing_provider', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['status', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"Pricing Audit: {self.pricing_provider} - {self.status} ({self.timestamp})"


class FeeCalculation(models.Model):
    """
    Fee calculation audit trail with deterministic results and source tracking

    Tracks all fee calculations for loan scenarios including:
    - Transfer taxes, recording fees, recordation taxes
    - Title fees, prepaids, escrows
    - UFMIP (FHA), MIP (FHA), VAFF (VA)

    Each fee has source attribution (system/AI/override) and calculation trace
    """
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fee_calculations'
    )
    loan_estimate = models.ForeignKey(
        'LoanEstimate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fee_calculations'
    )
    pricing_scenario = models.ForeignKey(
        PricingScenario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fee_calculations'
    )
    tax_data = models.ForeignKey(
        TaxData,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fee_calculations',
        help_text="TaxData version used for this calculation"
    )

    # Input parameters
    property_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Property value/purchase price"
    )
    loan_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Loan amount"
    )
    loan_type = models.CharField(
        max_length=20,
        choices=[
            ('conventional', 'Conventional'),
            ('fha', 'FHA'),
            ('va', 'VA'),
            ('usda', 'USDA'),
        ],
        default='conventional'
    )
    first_time_homebuyer = models.BooleanField(default=False)
    is_new_construction = models.BooleanField(default=False)
    closing_date = models.DateField(null=True, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)

    # Calculated totals
    total_transfer_taxes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_recording_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_recordation_taxes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_title_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_prepaids = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_escrows = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_mortgage_insurance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Detailed fee breakdown with source tracking
    fee_breakdown = models.JSONField(
        help_text="Complete fee breakdown with line items, sources, and calculation traces"
    )

    # Determinism and audit
    deterministic_hash = models.CharField(
        max_length=32,
        db_index=True,
        help_text="Hash of inputs for determinism verification"
    )
    jurisdiction = models.CharField(
        max_length=100,
        help_text="Jurisdiction (State-County) for this calculation"
    )
    tax_data_version = models.CharField(
        max_length=10,
        default="2.0",
        help_text="Tax data schema version used"
    )

    # Metadata
    calculation_timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-calculation_timestamp']
        indexes = [
            models.Index(fields=['user', '-calculation_timestamp']),
            models.Index(fields=['loan_estimate', '-calculation_timestamp']),
            models.Index(fields=['pricing_scenario', '-calculation_timestamp']),
            models.Index(fields=['deterministic_hash']),
            models.Index(fields=['jurisdiction', '-calculation_timestamp']),
            models.Index(fields=['-calculation_timestamp']),
        ]

    def __str__(self):
        return f"Fee Calc: {self.jurisdiction} - ${self.total_fees:,.2f} - {self.calculation_timestamp}"

    @property
    def has_overrides(self) -> bool:
        """Check if any fees have 'override' source"""
        breakdown = self.fee_breakdown
        for category in ['transfer_taxes', 'recording_fees', 'recordation_taxes',
                        'title_fees', 'prepaids', 'escrows', 'mortgage_insurance']:
            for item in breakdown.get(category, []):
                if item.get('source') == 'override':
                    return True
        return False

    @property
    def source_summary(self) -> dict:
        """Get count of fees by source type"""
        sources = {'system': 0, 'ai': 0, 'override': 0}
        breakdown = self.fee_breakdown

        for category in ['transfer_taxes', 'recording_fees', 'recordation_taxes',
                        'title_fees', 'prepaids', 'escrows', 'mortgage_insurance']:
            for item in breakdown.get(category, []):
                source = item.get('source', 'system')
                sources[source] = sources.get(source, 0) + 1

        return sources
