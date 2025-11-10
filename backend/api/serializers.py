"""
Serializers for API models
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    State, County, TaxData, Municipality,
    ScraperLog, UserProfile, LoanEstimate,
    CreditReport, Tradeline, AuditEvent, DocTask
)


class StateSerializer(serializers.ModelSerializer):
    """Serializer for State model"""
    county_count = serializers.SerializerMethodField()

    class Meta:
        model = State
        fields = ['id', 'code', 'name', 'active', 'county_count', 'created_at']
        read_only_fields = ['created_at']

    def get_county_count(self, obj):
        return obj.counties.filter(active=True).count()


class CountySerializer(serializers.ModelSerializer):
    """Serializer for County model"""
    state_name = serializers.CharField(source='state.name', read_only=True)
    state_code = serializers.CharField(source='state.code', read_only=True)
    has_tax_data = serializers.SerializerMethodField()

    class Meta:
        model = County
        fields = [
            'id', 'name', 'state', 'state_name', 'state_code',
            'fips_code', 'active', 'has_tax_data', 'created_at'
        ]
        read_only_fields = ['created_at']

    def get_has_tax_data(self, obj):
        return obj.tax_data.filter(is_current=True).exists()


class CountyDetailSerializer(CountySerializer):
    """Detailed County serializer with municipalities"""
    municipalities = serializers.SerializerMethodField()

    class Meta(CountySerializer.Meta):
        fields = CountySerializer.Meta.fields + ['municipalities']

    def get_municipalities(self, obj):
        return MunicipalitySerializer(
            obj.municipalities.filter(active=True),
            many=True
        ).data


class MunicipalitySerializer(serializers.ModelSerializer):
    """Serializer for Municipality model"""

    class Meta:
        model = Municipality
        fields = ['id', 'name', 'millage_rate', 'zip_codes', 'active']


class TaxDataSerializer(serializers.ModelSerializer):
    """Serializer for TaxData model"""
    state_code = serializers.CharField(source='state.code', read_only=True)
    state_name = serializers.CharField(source='state.name', read_only=True)
    county_name = serializers.CharField(source='county.name', read_only=True)
    is_stale = serializers.BooleanField(read_only=True)

    class Meta:
        model = TaxData
        fields = [
            'id', 'state', 'state_code', 'state_name',
            'county', 'county_name', 'version', 'is_current',
            'data_completeness', 'scraper_confidence',
            'data', 'effective_date', 'last_verified',
            'is_stale', 'sources', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'version', 'last_verified', 'created_at', 'updated_at'
        ]


class TaxDataListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing tax data (without full data JSON)"""
    state_code = serializers.CharField(source='state.code', read_only=True)
    county_name = serializers.CharField(source='county.name', read_only=True)
    is_stale = serializers.BooleanField(read_only=True)

    class Meta:
        model = TaxData
        fields = [
            'id', 'state_code', 'county_name', 'version',
            'is_current', 'data_completeness', 'scraper_confidence',
            'effective_date', 'last_verified', 'is_stale'
        ]


class ScraperLogSerializer(serializers.ModelSerializer):
    """Serializer for ScraperLog model"""
    state_code = serializers.CharField(source='state.code', read_only=True)
    county_name = serializers.CharField(source='county.name', read_only=True)
    triggered_by_username = serializers.CharField(
        source='triggered_by.username',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = ScraperLog
        fields = [
            'id', 'state', 'state_code', 'county', 'county_name',
            'status', 'started_at', 'completed_at', 'processing_time',
            'data_completeness', 'confidence_score', 'sources_found',
            'error_message', 'retry_count',
            'llm_provider', 'llm_model', 'tokens_used',
            'triggered_by', 'triggered_by_username', 'trigger_type'
        ]
        read_only_fields = ['started_at', 'completed_at', 'processing_time']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        # Create associated profile
        UserProfile.objects.create(user=user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'email',
            'default_state', 'default_county',
            'annual_income', 'credit_score',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class LoanEstimateSerializer(serializers.ModelSerializer):
    """Serializer for LoanEstimate model"""
    county_name = serializers.CharField(source='county.name', read_only=True)
    state_code = serializers.CharField(source='county.state.code', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    loan_to_value = serializers.FloatField(read_only=True)
    monthly_payment = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = LoanEstimate
        fields = [
            'id', 'user', 'username', 'name', 'is_saved',
            'property_address', 'county', 'county_name', 'state_code',
            'property_value', 'property_type',
            'loan_amount', 'down_payment', 'interest_rate',
            'loan_term_years', 'loan_type', 'first_time_homebuyer',
            'closing_date', 'calculation_results', 'tax_data',
            'loan_to_value', 'monthly_payment',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'calculation_results']

    def validate_down_payment(self, value):
        """Ensure down payment is not negative"""
        if value < 0:
            raise serializers.ValidationError("Down payment cannot be negative.")
        return value

    def validate_interest_rate(self, value):
        """Ensure interest rate is reasonable"""
        if value < 0 or value > 20:
            raise serializers.ValidationError("Interest rate must be between 0% and 20%.")
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        if 'loan_amount' in attrs and 'property_value' in attrs:
            if attrs['loan_amount'] > attrs['property_value']:
                raise serializers.ValidationError({
                    "loan_amount": "Loan amount cannot exceed property value."
                })

        if 'down_payment' in attrs and 'property_value' in attrs and 'loan_amount' in attrs:
            expected_loan = attrs['property_value'] - attrs['down_payment']
            if abs(attrs['loan_amount'] - expected_loan) > 1:  # Allow for rounding
                raise serializers.ValidationError({
                    "loan_amount": "Loan amount should equal property value minus down payment."
                })

        return attrs


class LoanEstimateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing loan estimates"""
    county_name = serializers.CharField(source='county.name', read_only=True)
    state_code = serializers.CharField(source='county.state.code', read_only=True)
    monthly_payment = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = LoanEstimate
        fields = [
            'id', 'name', 'is_saved', 'property_address',
            'county_name', 'state_code', 'property_value',
            'loan_amount', 'loan_type', 'monthly_payment',
            'created_at'
        ]


class LoanEstimateCreateSerializer(serializers.Serializer):
    """Serializer for creating a new loan estimate calculation"""
    # Property information
    property_address = serializers.CharField(required=False, allow_blank=True)
    county_id = serializers.IntegerField()
    property_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    property_type = serializers.ChoiceField(choices=LoanEstimate.PROPERTY_TYPE_CHOICES)

    # Loan details
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    down_payment = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=3)
    loan_term_years = serializers.IntegerField(default=30)
    loan_type = serializers.ChoiceField(choices=LoanEstimate.LOAN_TYPE_CHOICES)

    # Buyer information
    first_time_homebuyer = serializers.BooleanField(default=False)
    closing_date = serializers.DateField()

    # Optional: ZIP code for municipality tax overlay
    zip_code = serializers.CharField(max_length=10, required=False, allow_blank=True)

    # Save preference
    save_estimate = serializers.BooleanField(default=False)
    estimate_name = serializers.CharField(required=False, allow_blank=True)

    def validate_county_id(self, value):
        """Ensure county exists"""
        if not County.objects.filter(id=value, active=True).exists():
            raise serializers.ValidationError("Invalid county ID.")
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        if attrs['loan_amount'] > attrs['property_value']:
            raise serializers.ValidationError({
                "loan_amount": "Loan amount cannot exceed property value."
            })

        expected_loan = attrs['property_value'] - attrs['down_payment']
        if abs(attrs['loan_amount'] - expected_loan) > 1:
            raise serializers.ValidationError({
                "loan_amount": "Loan amount should equal property value minus down payment."
            })

        if attrs['interest_rate'] < 0 or attrs['interest_rate'] > 20:
            raise serializers.ValidationError({
                "interest_rate": "Interest rate must be between 0% and 20%."
            })

        return attrs


class TradelineSerializer(serializers.ModelSerializer):
    """Serializer for Tradeline model with normalized credit fields."""
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    confirmation_status_display = serializers.CharField(
        source='get_confirmation_status_display',
        read_only=True
    )
    has_recent_lates = serializers.BooleanField(read_only=True)
    total_lates_24mo = serializers.IntegerField(read_only=True)
    needs_confirmation = serializers.BooleanField(read_only=True)

    class Meta:
        model = Tradeline
        fields = [
            'id', 'credit_report',
            # Account info
            'account_type', 'account_type_display',
            'creditor_name', 'account_number',
            # Balance and payment
            'current_balance', 'monthly_payment', 'credit_limit',
            # Status
            'status', 'status_display',
            'opened_date', 'last_payment_date', 'days_past_due',
            # DLA tracking (24 months)
            'lates_30_count_24mo', 'lates_60_count_24mo', 'lates_90_count_24mo',
            # DLA tracking (36 months)
            'lates_30_count_36mo', 'lates_60_count_36mo', 'lates_90_count_36mo',
            # Flags
            'is_deferred', 'is_ibr', 'is_cosigned', 'is_disputed',
            'has_less_than_10_payments',
            # Payment metadata
            'payment_count', 'months_reviewed', 'remarks',
            # Confirmation workflow
            'confirmation_status', 'confirmation_status_display',
            'confirmed_at', 'dispute_reason',
            # Computed properties
            'has_recent_lates', 'total_lates_24mo', 'needs_confirmation',
            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'confirmed_at']


class CreditReportSerializer(serializers.ModelSerializer):
    """Serializer for CreditReport model with tradelines."""
    username = serializers.CharField(source='user.username', read_only=True)
    bureau_display = serializers.CharField(source='get_bureau_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    middle_score = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    tradelines = TradelineSerializer(many=True, read_only=True)

    class Meta:
        model = CreditReport
        fields = [
            'id', 'user', 'username', 'loan_estimate',
            # Bureau info
            'bureau', 'bureau_display', 'status', 'status_display',
            'report_id', 'report_date',
            # Credit scores
            'equifax_score', 'experian_score', 'transunion_score', 'middle_score',
            # Summary stats
            'total_tradelines', 'total_inquiries', 'total_monthly_debt',
            # Expiration
            'expires_at', 'is_expired',
            # Error handling
            'error_message',
            # Timestamps
            'created_at', 'updated_at',
            # Related
            'tradelines'
        ]
        read_only_fields = [
            'id', 'report_date', 'middle_score', 'is_expired',
            'created_at', 'updated_at', 'tradelines'
        ]


class CreditReportListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing credit reports (without tradelines)."""
    username = serializers.CharField(source='user.username', read_only=True)
    middle_score = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = CreditReport
        fields = [
            'id', 'user', 'username', 'bureau', 'status',
            'report_date', 'middle_score',
            'total_tradelines', 'total_inquiries', 'total_monthly_debt',
            'is_expired', 'created_at'
        ]


class AuditEventSerializer(serializers.ModelSerializer):
    """Serializer for AuditEvent model."""
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True, allow_null=True)

    class Meta:
        model = AuditEvent
        fields = [
            'id', 'event_type', 'event_type_display', 'timestamp',
            'user', 'username', 'borrower_name', 'ssn_last_four',
            'ip_address', 'user_agent',
            'loan_estimate', 'context'
        ]
        read_only_fields = ['id', 'timestamp']


class DocTaskSerializer(serializers.ModelSerializer):
    """Serializer for DocTask model with full CRUD support."""
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    reviewed_by_username = serializers.CharField(
        source='reviewed_by.username',
        read_only=True,
        allow_null=True
    )
    is_overdue = serializers.BooleanField(read_only=True)

    # Related object details
    tradeline_details = serializers.SerializerMethodField()

    class Meta:
        model = DocTask
        fields = [
            'id', 'user', 'username',
            'loan_estimate', 'tradeline', 'tradeline_details',
            # Task info
            'task_type', 'task_type_display',
            'status', 'status_display',
            'title', 'description',
            # Borrower response
            'borrower_notes', 'uploaded_documents',
            # Admin review
            'reviewed_by', 'reviewed_by_username', 'admin_notes',
            # Timestamps
            'created_at', 'due_date', 'completed_at', 'updated_at',
            # Computed
            'is_overdue'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at', 'completed_at'
        ]

    def get_tradeline_details(self, obj):
        """Return basic tradeline info if task is linked to a tradeline."""
        if obj.tradeline:
            return {
                'id': obj.tradeline.id,
                'account_type': obj.tradeline.get_account_type_display(),
                'creditor_name': obj.tradeline.creditor_name,
                'current_balance': str(obj.tradeline.current_balance)
            }
        return None


class DocTaskListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing doc tasks."""
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = DocTask
        fields = [
            'id', 'user', 'username',
            'task_type', 'task_type_display',
            'status', 'status_display',
            'title', 'due_date', 'is_overdue',
            'created_at', 'updated_at'
        ]


class DocTaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating doc tasks (admin/system use)."""

    class Meta:
        model = DocTask
        fields = [
            'user', 'loan_estimate', 'tradeline',
            'task_type', 'title', 'description', 'due_date'
        ]

    def validate(self, attrs):
        """Validate that tradeline belongs to user if specified."""
        if attrs.get('tradeline') and attrs.get('user'):
            tradeline = attrs['tradeline']
            user = attrs['user']
            if tradeline.credit_report.user != user:
                raise serializers.ValidationError({
                    'tradeline': 'Tradeline must belong to the specified user.'
                })
        return attrs


class DocTaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer for borrower updating their doc task (response)."""

    class Meta:
        model = DocTask
        fields = ['borrower_notes', 'uploaded_documents', 'status']

    def validate_status(self, value):
        """Only allow status transitions from pending->in_progress or in_progress->completed."""
        instance = self.instance
        if instance:
            current_status = instance.status
            # Borrower can only move to in_progress or completed
            if value not in ['in_progress', 'completed']:
                raise serializers.ValidationError(
                    "Borrowers can only set status to 'in_progress' or 'completed'."
                )
            # Validate transition
            if current_status == 'pending' and value not in ['in_progress', 'completed']:
                raise serializers.ValidationError(
                    "Can only transition from 'pending' to 'in_progress' or 'completed'."
                )
            if current_status == 'in_progress' and value not in ['in_progress', 'completed']:
                raise serializers.ValidationError(
                    "Can only transition from 'in_progress' to 'completed'."
                )
            if current_status == 'completed':
                raise serializers.ValidationError(
                    "Cannot change status of completed task."
                )
            if current_status == 'cancelled':
                raise serializers.ValidationError(
                    "Cannot change status of cancelled task."
                )
        return value


class DocTaskAdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin updating doc task (review/cancel)."""

    class Meta:
        model = DocTask
        fields = ['status', 'admin_notes', 'reviewed_by']

    def validate_status(self, value):
        """Admin can transition to any status except restricting completed."""
        instance = self.instance
        if instance and instance.status == 'completed' and value != 'completed':
            # Allow admin to reopen tasks if needed
            pass
        return value
