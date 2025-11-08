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
    ScraperLog, UserProfile, LoanEstimate
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


# Customize admin site
admin.site.site_header = "Mortgage Calculator Admin"
admin.site.site_title = "Mortgage Calculator"
admin.site.index_title = "Administration"
