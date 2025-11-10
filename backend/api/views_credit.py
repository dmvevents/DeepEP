"""
Credit Report ViewSets with PII access logging and audit trails.

Implements RBAC, audit logging for all credit report access, and SSN masking.
"""
import json
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes as perm_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .models import CreditReport, Tradeline, AuditEvent
from .serializers import (
    CreditReportSerializer,
    CreditReportListSerializer,
    TradelineSerializer
)
from . import credit_parser


@csrf_exempt
def parse_credit(request):
    """
    Parse credit report data endpoint.
    Accepts POST with credit report payload, returns normalized data.
    Minimal stub for Phase 1 - just echoes back the payload with status.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    try:
        payload = json.loads(request.body.decode("utf-8"))
        # Minimal response - just acknowledge receipt
        result = {
            "status": "received",
            "data": payload,
            "message": "Credit data received successfully"
        }
        return JsonResponse(result, status=200, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


class CreditReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CreditReport model with PII access logging.

    Security Features:
    - SSN encrypted at rest (AES-128)
    - SSN masked in all responses (***-**-1234)
    - Audit log for all credit report access
    - RBAC: Users see only their own reports, staff see all
    """
    queryset = CreditReport.objects.all().select_related(
        'user', 'loan_estimate'
    ).prefetch_related('tradelines')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'bureau', 'status', 'loan_estimate']
    ordering_fields = ['report_date', 'created_at']
    ordering = ['-report_date']

    def get_queryset(self):
        """Filter credit reports based on user role."""
        user = self.request.user
        if user.is_staff:
            # Staff can see all reports
            return self.queryset
        # Borrowers can only see their own reports
        return self.queryset.filter(user=user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return CreditReportListSerializer
        return CreditReportSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve credit report with audit logging.
        Logs PII access event for compliance.
        """
        instance = self.get_object()

        # Log audit event for PII access
        self._log_credit_access(
            event_type='credit_pull',
            credit_report=instance,
            context={'action': 'retrieve', 'full_report': True}
        )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """
        List credit reports (no audit log for list view since SSN not exposed).
        """
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Create new credit report with SSN encryption and audit logging.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        credit_report = serializer.save()

        # Log audit event for credit consent
        self._log_credit_access(
            event_type='credit_consent',
            credit_report=credit_report,
            context={'action': 'create', 'bureau': credit_report.bureau}
        )

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        """Update credit report with audit logging."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        credit_report = serializer.save()

        # Log audit event
        self._log_credit_access(
            event_type='pii_access',
            credit_report=credit_report,
            context={'action': 'update', 'partial': partial}
        )

        return Response(serializer.data)

    @extend_schema(
        summary="Get tradelines for credit report",
        responses={200: TradelineSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def tradelines(self, request, pk=None):
        """
        Get all tradelines for a credit report.
        Logs PII access since account numbers may be visible.
        """
        credit_report = self.get_object()

        # Log audit event
        self._log_credit_access(
            event_type='pii_access',
            credit_report=credit_report,
            context={'action': 'view_tradelines', 'tradeline_count': credit_report.tradelines.count()}
        )

        tradelines = credit_report.tradelines.all()
        serializer = TradelineSerializer(tradelines, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get credit report summary (scores only)",
        responses={200: {'type': 'object'}}
    )
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """
        Get credit report summary without PII (no audit log required).
        Returns only scores and aggregate statistics.
        """
        credit_report = self.get_object()

        summary_data = {
            'id': credit_report.id,
            'report_date': credit_report.report_date,
            'bureau': credit_report.get_bureau_display(),
            'status': credit_report.get_status_display(),
            'equifax_score': credit_report.equifax_score,
            'experian_score': credit_report.experian_score,
            'transunion_score': credit_report.transunion_score,
            'middle_score': credit_report.middle_score,
            'total_tradelines': credit_report.total_tradelines,
            'total_inquiries': credit_report.total_inquiries,
            'total_monthly_debt': credit_report.total_monthly_debt,
            'is_expired': credit_report.is_expired,
        }

        return Response(summary_data)

    def _log_credit_access(self, event_type, credit_report, context=None):
        """
        Helper to log audit events for credit report access.

        Args:
            event_type: Type of audit event ('credit_pull', 'credit_consent', 'pii_access')
            credit_report: CreditReport instance
            context: Additional context data
        """
        try:
            # Get SSN last 4 for audit trail (masked)
            ssn_last_four = ''
            ssn = credit_report.get_ssn()
            if ssn and len(ssn) >= 4:
                ssn_last_four = ssn[-4:]

            event_context = {
                'credit_report_id': credit_report.id,
                'bureau': credit_report.bureau,
                'report_date': credit_report.report_date.isoformat(),
                **(context or {})
            }

            # Create immutable audit event
            AuditEvent.objects.create(
                event_type=event_type,
                user=self.request.user if hasattr(self, 'request') else None,
                borrower_name=credit_report.user.get_full_name() or credit_report.user.username,
                ssn_last_four=ssn_last_four,
                loan_estimate=credit_report.loan_estimate,
                ip_address=self._get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:255] if hasattr(self, 'request') else '',
                context=event_context
            )
        except Exception as e:
            # Log error but don't fail the request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create credit access audit event: {e}")

    def _get_client_ip(self):
        """Get client IP address from request."""
        if not hasattr(self, 'request'):
            return None
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class TradelineViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Tradeline model with confirmation workflow.

    Security: Account numbers are masked (last 4 digits only).
    """
    queryset = Tradeline.objects.all().select_related('credit_report', 'credit_report__user')
    serializer_class = TradelineSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['credit_report', 'account_type', 'status', 'confirmation_status']
    ordering_fields = ['current_balance', 'monthly_payment', 'opened_date']
    ordering = ['-current_balance']

    def get_queryset(self):
        """Filter tradelines based on user role."""
        user = self.request.user
        if user.is_staff:
            return self.queryset
        # Borrowers can only see tradelines from their own credit reports
        return self.queryset.filter(credit_report__user=user)

    @extend_schema(
        summary="Confirm tradeline (borrower action)",
        responses={200: TradelineSerializer}
    )
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Borrower confirms tradeline is accurate.
        Updates confirmation_status to 'confirmed'.
        """
        tradeline = self.get_object()

        # Only tradeline owner can confirm
        if tradeline.credit_report.user != request.user:
            return Response(
                {"detail": "You can only confirm your own tradelines."},
                status=status.HTTP_403_FORBIDDEN
            )

        tradeline.confirmation_status = 'confirmed'
        tradeline.confirmed_at = timezone.now()
        tradeline.save(update_fields=['confirmation_status', 'confirmed_at'])

        serializer = self.get_serializer(tradeline)
        return Response(serializer.data)

    @extend_schema(
        summary="Dispute tradeline (borrower action)",
        request={'application/json': {'type': 'object', 'properties': {'dispute_reason': {'type': 'string'}}}},
        responses={200: TradelineSerializer}
    )
    @action(detail=True, methods=['post'])
    def dispute(self, request, pk=None):
        """
        Borrower disputes tradeline accuracy.
        Updates confirmation_status to 'disputed' and creates doc task.
        """
        tradeline = self.get_object()

        # Only tradeline owner can dispute
        if tradeline.credit_report.user != request.user:
            return Response(
                {"detail": "You can only dispute your own tradelines."},
                status=status.HTTP_403_FORBIDDEN
            )

        dispute_reason = request.data.get('dispute_reason', '')
        if not dispute_reason:
            return Response(
                {"detail": "dispute_reason is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        tradeline.confirmation_status = 'disputed'
        tradeline.dispute_reason = dispute_reason
        tradeline.confirmed_at = timezone.now()
        tradeline.save(update_fields=['confirmation_status', 'dispute_reason', 'confirmed_at'])

        # Create doc task for dispute resolution
        from .models import DocTask
        DocTask.objects.create(
            user=request.user,
            loan_estimate=tradeline.credit_report.loan_estimate,
            tradeline=tradeline,
            task_type='dispute_tradeline',
            title=f"Dispute: {tradeline.creditor_name}",
            description=f"Borrower disputed tradeline. Reason: {dispute_reason}"
        )

        serializer = self.get_serializer(tradeline)
        return Response(serializer.data)
