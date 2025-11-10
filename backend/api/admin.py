"""
Django admin configuration for API models
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json
from .models import (
    State, County, TaxData, Municipality,
    ScraperLog, UserProfile, LoanEstimate, DocTask,
    CreditReport, Tradeline, AuditEvent, FeeCalculation
)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'active', 'county_count', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['code', 'name']
    ordering = ['name']

    def county_count(self, obj):
        count = obj.counties.filter(active=True).count()
        return count
    county_count.short_description = 'Active Counties'


@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'fips_code', 'active', 'has_tax_data', 'created_at']
    list_filter = ['active', 'state', 'created_at']
    search_fields = ['name', 'fips_code', 'state__name']
    ordering = ['state__name', 'name']
    raw_id_fields = ['state']

    def has_tax_data(self, obj):
        has_data = obj.tax_data.filter(is_current=True).exists()
        if has_data:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    has_tax_data.short_description = 'Has Data'
    has_tax_data.admin_order_field = 'tax_data'


@admin.register(TaxData)
class TaxDataAdmin(admin.ModelAdmin):
    list_display = [
        'county', 'state', 'version', 'is_current',
        'data_completeness_display', 'confidence_display',
        'last_verified', 'is_stale_display'
    ]
    list_filter = [
        'is_current', 'state', 'last_verified',
        'data_completeness', 'scraper_confidence'
    ]
    search_fields = ['county__name', 'state__name', 'notes']
    readonly_fields = [
        'last_verified', 'created_at', 'updated_at',
        'formatted_data', 'formatted_sources'
    ]
    fieldsets = (
        ('Location', {
            'fields': ('state', 'county')
        }),
        ('Version Information', {
            'fields': ('version', 'is_current', 'effective_date')
        }),
        ('Quality Metrics', {
            'fields': ('data_completeness', 'scraper_confidence')
        }),
        ('Data', {
            'fields': ('data', 'formatted_data'),
            'classes': ('collapse',)
        }),
        ('Sources', {
            'fields': ('sources', 'formatted_sources', 'notes')
        }),
        ('Timestamps', {
            'fields': ('last_verified', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    raw_id_fields = ['state', 'county']
    date_hierarchy = 'last_verified'

    def data_completeness_display(self, obj):
        color = 'green' if obj.data_completeness >= 90 else 'orange' if obj.data_completeness >= 70 else 'red'
        return format_html(
            '<span style="color: {};">{}</span>%',
            color, obj.data_completeness
        )
    data_completeness_display.short_description = 'Completeness'
    data_completeness_display.admin_order_field = 'data_completeness'

    def confidence_display(self, obj):
        color = 'green' if obj.scraper_confidence >= 80 else 'orange' if obj.scraper_confidence >= 60 else 'red'
        return format_html(
            '<span style="color: {};">{}</span>%',
            color, obj.scraper_confidence
        )
    confidence_display.short_description = 'Confidence'
    confidence_display.admin_order_field = 'scraper_confidence'

    def is_stale_display(self, obj):
        if obj.is_stale:
            return format_html('<span style="color: red;">Stale</span>')
        return format_html('<span style="color: green;">Fresh</span>')
    is_stale_display.short_description = 'Status'

    def formatted_data(self, obj):
        return mark_safe(f'<pre>{json.dumps(obj.data, indent=2)}</pre>')
    formatted_data.short_description = 'Data (Formatted)'

    def formatted_sources(self, obj):
        if not obj.sources:
            return "No sources"
        html = '<ul>'
        for source in obj.sources:
            html += f'<li><a href="{source}" target="_blank">{source}</a></li>'
        html += '</ul>'
        return mark_safe(html)
    formatted_sources.short_description = 'Sources (Links)'


@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ['name', 'county', 'millage_rate', 'zip_code_count', 'active']
    list_filter = ['active', 'county__state']
    search_fields = ['name', 'county__name']
    raw_id_fields = ['county']

    def zip_code_count(self, obj):
        return len(obj.zip_codes)
    zip_code_count.short_description = 'Zip Codes'


@admin.register(ScraperLog)
class ScraperLogAdmin(admin.ModelAdmin):
    list_display = [
        'county', 'state', 'status', 'trigger_type',
        'processing_time', 'data_completeness',
        'started_at', 'retry_count'
    ]
    list_filter = [
        'status', 'trigger_type', 'llm_provider',
        'state', 'started_at'
    ]
    search_fields = ['county__name', 'state__name', 'error_message']
    readonly_fields = [
        'started_at', 'completed_at', 'processing_time',
        'tokens_used', 'sources_found'
    ]
    fieldsets = (
        ('Location', {
            'fields': ('state', 'county')
        }),
        ('Status', {
            'fields': ('status', 'trigger_type', 'triggered_by', 'retry_count')
        }),
        ('Results', {
            'fields': (
                'data_completeness', 'confidence_score',
                'sources_found', 'error_message'
            )
        }),
        ('LLM Information', {
            'fields': ('llm_provider', 'llm_model', 'tokens_used'),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'processing_time')
        }),
    )
    raw_id_fields = ['state', 'county', 'triggered_by']
    date_hierarchy = 'started_at'

    def has_add_permission(self, request):
        # Scraper logs should only be created by the system
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'default_county', 'created_at']
    search_fields = ['user__username', 'user__email']
    raw_id_fields = ['user', 'default_state', 'default_county']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LoanEstimate)
class LoanEstimateAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'county', 'property_value', 'loan_amount',
        'loan_type', 'is_saved', 'created_at'
    ]
    list_filter = [
        'loan_type', 'property_type', 'first_time_homebuyer',
        'is_saved', 'created_at'
    ]
    search_fields = ['user__username', 'property_address', 'name']
    readonly_fields = [
        'created_at', 'updated_at', 'loan_to_value',
        'monthly_payment', 'formatted_results'
    ]
    fieldsets = (
        ('User', {
            'fields': ('user', 'name', 'is_saved')
        }),
        ('Property', {
            'fields': (
                'property_address', 'county', 'property_value',
                'property_type'
            )
        }),
        ('Loan Details', {
            'fields': (
                'loan_amount', 'down_payment', 'interest_rate',
                'loan_term_years', 'loan_type', 'first_time_homebuyer'
            )
        }),
        ('Dates', {
            'fields': ('closing_date', 'created_at', 'updated_at')
        }),
        ('Calculations', {
            'fields': (
                'tax_data', 'loan_to_value', 'monthly_payment',
                'calculation_results', 'formatted_results'
            ),
            'classes': ('collapse',)
        }),
    )
    raw_id_fields = ['user', 'county', 'tax_data']
    date_hierarchy = 'created_at'

    def formatted_results(self, obj):
        return mark_safe(f'<pre>{json.dumps(obj.calculation_results, indent=2)}</pre>')
    formatted_results.short_description = 'Calculation Results (Formatted)'


@admin.register(DocTask)
class DocTaskAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'task_type', 'status', 'title',
        'due_date', 'is_overdue_display', 'created_at'
    ]
    list_filter = [
        'status', 'task_type', 'created_at', 'due_date'
    ]
    search_fields = [
        'user__username', 'title', 'description',
        'borrower_notes', 'admin_notes'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'completed_at',
        'is_overdue', 'formatted_uploaded_documents'
    ]
    fieldsets = (
        ('Task Information', {
            'fields': (
                'user', 'loan_estimate', 'tradeline',
                'task_type', 'status', 'title', 'description', 'due_date'
            )
        }),
        ('Borrower Response', {
            'fields': (
                'borrower_notes', 'uploaded_documents',
                'formatted_uploaded_documents'
            ),
            'classes': ('collapse',)
        }),
        ('Admin Review', {
            'fields': ('reviewed_by', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at', 'updated_at', 'is_overdue'),
            'classes': ('collapse',)
        }),
    )
    raw_id_fields = ['user', 'loan_estimate', 'tradeline', 'reviewed_by']
    date_hierarchy = 'created_at'
    actions = ['mark_completed', 'mark_in_progress', 'mark_cancelled']

    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">⚠ Overdue</span>')
        elif obj.status == 'completed':
            return format_html('<span style="color: green;">✓ Done</span>')
        return format_html('<span style="color: gray;">-</span>')
    is_overdue_display.short_description = 'Status'

    def formatted_uploaded_documents(self, obj):
        if not obj.uploaded_documents:
            return "No documents uploaded"
        return mark_safe(f'<pre>{json.dumps(obj.uploaded_documents, indent=2)}</pre>')
    formatted_uploaded_documents.short_description = 'Uploaded Documents (Formatted)'

    @admin.action(description='Mark selected tasks as completed')
    def mark_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.exclude(status='completed').update(
            status='completed',
            completed_at=timezone.now(),
            reviewed_by=request.user
        )
        self.message_user(request, f"{updated} tasks marked as completed.")

    @admin.action(description='Mark selected tasks as in progress')
    def mark_in_progress(self, request, queryset):
        updated = queryset.exclude(status='in_progress').update(status='in_progress')
        self.message_user(request, f"{updated} tasks marked as in progress.")

    @admin.action(description='Cancel selected tasks')
    def mark_cancelled(self, request, queryset):
        updated = queryset.exclude(status='cancelled').update(
            status='cancelled',
            reviewed_by=request.user
        )
        self.message_user(request, f"{updated} tasks cancelled.")


@admin.register(CreditReport)
class CreditReportAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'bureau', 'status', 'middle_score',
        'total_tradelines', 'report_date'
    ]
    list_filter = ['bureau', 'status', 'report_date']
    search_fields = ['user__username', 'report_id']
    readonly_fields = [
        'middle_score', 'is_expired', 'report_date',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['user', 'loan_estimate']
    date_hierarchy = 'report_date'


@admin.register(Tradeline)
class TradelineAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'credit_report', 'account_type', 'creditor_name',
        'current_balance', 'monthly_payment', 'confirmation_status',
        'has_recent_lates'
    ]
    list_filter = [
        'account_type', 'status', 'confirmation_status',
        'is_deferred', 'is_ibr', 'has_less_than_10_payments'
    ]
    search_fields = ['creditor_name', 'account_number']
    readonly_fields = [
        'has_recent_lates', 'total_lates_24mo', 'needs_confirmation',
        'created_at', 'updated_at', 'confirmed_at'
    ]
    raw_id_fields = ['credit_report']
    date_hierarchy = 'created_at'


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'event_type', 'user', 'borrower_name',
        'timestamp', 'ip_address'
    ]
    list_filter = ['event_type', 'timestamp']
    search_fields = [
        'borrower_name', 'ssn_last_four', 'user__username'
    ]
    readonly_fields = [
        'event_type', 'timestamp', 'user', 'borrower_name',
        'ssn_last_four', 'ip_address', 'user_agent',
        'loan_estimate', 'context', 'formatted_context'
    ]
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'timestamp', 'user', 'borrower_name')
        }),
        ('Security', {
            'fields': ('ssn_last_four', 'ip_address', 'user_agent')
        }),
        ('Related Objects', {
            'fields': ('loan_estimate',)
        }),
        ('Context', {
            'fields': ('context', 'formatted_context'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        # Audit events should only be created by the system
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of audit trail
        return request.user.is_superuser

    def formatted_context(self, obj):
        if not obj.context:
            return "No context data"
        return mark_safe(f'<pre>{json.dumps(obj.context, indent=2)}</pre>')
    formatted_context.short_description = 'Context (Formatted)'


@admin.register(FeeCalculation)
class FeeCalculationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'jurisdiction', 'loan_type',
        'total_fees_display', 'has_overrides_display',
        'calculation_timestamp'
    ]
    list_filter = [
        'loan_type', 'first_time_homebuyer', 'is_new_construction',
        'jurisdiction', 'calculation_timestamp'
    ]
    search_fields = [
        'user__username', 'jurisdiction', 'deterministic_hash'
    ]
    readonly_fields = [
        'calculation_timestamp', 'updated_at', 'deterministic_hash',
        'jurisdiction', 'tax_data_version', 'has_overrides',
        'source_summary_display', 'formatted_fee_breakdown',
        'total_transfer_taxes', 'total_recording_fees',
        'total_recordation_taxes', 'total_title_fees',
        'total_prepaids', 'total_escrows', 'total_mortgage_insurance',
        'total_fees'
    ]
    fieldsets = (
        ('User & Relationships', {
            'fields': ('user', 'loan_estimate', 'pricing_scenario', 'tax_data')
        }),
        ('Input Parameters', {
            'fields': (
                'property_value', 'loan_amount', 'loan_type',
                'first_time_homebuyer', 'is_new_construction',
                'closing_date', 'zip_code'
            )
        }),
        ('Totals', {
            'fields': (
                'total_transfer_taxes', 'total_recording_fees',
                'total_recordation_taxes', 'total_title_fees',
                'total_prepaids', 'total_escrows',
                'total_mortgage_insurance', 'total_fees'
            )
        }),
        ('Fee Breakdown', {
            'fields': ('fee_breakdown', 'formatted_fee_breakdown'),
            'classes': ('collapse',)
        }),
        ('Audit Trail', {
            'fields': (
                'deterministic_hash', 'jurisdiction', 'tax_data_version',
                'has_overrides', 'source_summary_display',
                'calculation_timestamp', 'updated_at'
            )
        }),
    )
    raw_id_fields = ['user', 'loan_estimate', 'pricing_scenario', 'tax_data']
    date_hierarchy = 'calculation_timestamp'

    def total_fees_display(self, obj):
        return f"${obj.total_fees:,.2f}"
    total_fees_display.short_description = 'Total Fees'
    total_fees_display.admin_order_field = 'total_fees'

    def has_overrides_display(self, obj):
        if obj.has_overrides:
            return format_html('<span style="color: orange;">⚠ Override</span>')
        return format_html('<span style="color: green;">✓ System</span>')
    has_overrides_display.short_description = 'Source'

    def source_summary_display(self, obj):
        summary = obj.source_summary
        html = '<ul style="margin: 0; padding-left: 20px;">'
        html += f'<li><strong>System:</strong> {summary["system"]} fees</li>'
        html += f'<li><strong>AI:</strong> {summary["ai"]} fees</li>'
        html += f'<li><strong>Override:</strong> {summary["override"]} fees</li>'
        html += '</ul>'
        return mark_safe(html)
    source_summary_display.short_description = 'Source Summary'

    def formatted_fee_breakdown(self, obj):
        return mark_safe(f'<pre>{json.dumps(obj.fee_breakdown, indent=2)}</pre>')
    formatted_fee_breakdown.short_description = 'Fee Breakdown (Formatted)'

    def has_add_permission(self, request):
        # Fee calculations should only be created by the system
        return False


# Customize admin site
admin.site.site_header = "Mortgage Calculator Admin"
admin.site.site_title = "Mortgage Calculator"
admin.site.index_title = "Administration"
