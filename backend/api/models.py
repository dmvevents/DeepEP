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
