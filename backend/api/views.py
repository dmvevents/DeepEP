"""
API Views for mortgage calculator
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import (
    State, County, TaxData, Municipality,
    ScraperLog, UserProfile, LoanEstimate, DocTask, AuditEvent
)
from .serializers import (
    StateSerializer, CountySerializer, CountyDetailSerializer,
    TaxDataSerializer, TaxDataListSerializer,
    MunicipalitySerializer, ScraperLogSerializer,
    UserSerializer, UserRegistrationSerializer,
    UserProfileSerializer, LoanEstimateSerializer,
    LoanEstimateListSerializer, DocTaskSerializer,
    DocTaskListSerializer, DocTaskCreateSerializer,
    DocTaskUpdateSerializer, DocTaskAdminUpdateSerializer
)


class StateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for State model
    """
    queryset = State.objects.filter(active=True)
    serializer_class = StateSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name']
    ordering_fields = ['name', 'code']
    ordering = ['name']

    @extend_schema(
        summary="Get counties for a state",
        responses={200: CountySerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def counties(self, request, pk=None):
        """Get all counties for a specific state"""
        state = self.get_object()
        counties = state.counties.filter(active=True)

        # Filter by search query if provided
        search = request.query_params.get('search', None)
        if search:
            counties = counties.filter(name__icontains=search)

        serializer = CountySerializer(counties, many=True)
        return Response(serializer.data)


class CountyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for County model
    """
    queryset = County.objects.filter(active=True).select_related('state')
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['state', 'state__code']
    search_fields = ['name', 'fips_code']
    ordering_fields = ['name', 'state__name']
    ordering = ['state__name', 'name']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CountyDetailSerializer
        return CountySerializer

    @extend_schema(
        summary="Get current tax data for a county",
        responses={200: TaxDataSerializer}
    )
    @action(detail=True, methods=['get'])
    def tax_data(self, request, pk=None):
        """Get current tax data for a county"""
        county = self.get_object()

        # Try to get current tax data
        tax_data = county.tax_data.filter(is_current=True).first()

        if not tax_data:
            return Response(
                {"detail": "No tax data available for this county yet."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if data is stale and trigger rescrape if enabled
        if tax_data.is_stale:
            from django.conf import settings
            if getattr(settings, 'ENABLE_AUTO_RESCRAPE', True):
                # Trigger async scraping task
                from scraper_integration.tasks import scrape_county_data
                scrape_county_data.delay(county.state.code, county.name)

        serializer = TaxDataSerializer(tax_data)
        return Response(serializer.data)


class TaxDataViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for TaxData model
    """
    queryset = TaxData.objects.all().select_related('state', 'county')
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['state', 'county', 'is_current', 'version']
    ordering_fields = ['last_verified', 'effective_date', 'data_completeness']
    ordering = ['-last_verified']

    def get_serializer_class(self):
        if self.action == 'list':
            return TaxDataListSerializer
        return TaxDataSerializer

    @extend_schema(
        summary="Get tax data by state and county codes",
        parameters=[
            OpenApiParameter('state_code', str, description='Two-letter state code'),
            OpenApiParameter('county_name', str, description='County name'),
        ]
    )
    @action(detail=False, methods=['get'], url_path='by-location/(?P<state_code>[^/.]+)/(?P<county_name>[^/.]+)')
    def by_location(self, request, state_code=None, county_name=None):
        """Get tax data by state code and county name"""
        try:
            state = State.objects.get(code=state_code.upper(), active=True)
            county = County.objects.get(
                state=state,
                name__iexact=county_name,
                active=True
            )
        except (State.DoesNotExist, County.DoesNotExist):
            return Response(
                {"detail": "State or county not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        tax_data = county.tax_data.filter(is_current=True).first()

        if not tax_data:
            return Response(
                {
                    "detail": "No tax data available for this county yet.",
                    "state": state_code,
                    "county": county_name
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TaxDataSerializer(tax_data)
        return Response(serializer.data)


class MunicipalityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Municipality model
    """
    queryset = Municipality.objects.filter(active=True).select_related('county')
    serializer_class = MunicipalitySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['county']
    search_fields = ['name', 'zip_codes']


class ScraperLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ScraperLog model (admin/monitoring)
    """
    queryset = ScraperLog.objects.all().select_related('state', 'county', 'triggered_by')
    serializer_class = ScraperLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['state', 'county', 'status', 'trigger_type']
    ordering_fields = ['started_at', 'processing_time', 'data_completeness']
    ordering = ['-started_at']

    @extend_schema(
        summary="Get scraper statistics"
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get overall scraper statistics"""
        from django.db.models import Avg, Count, Q
        from datetime import timedelta
        from django.utils import timezone

        # Last 24 hours
        last_24h = timezone.now() - timedelta(hours=24)

        stats = {
            'total_scrapes': ScraperLog.objects.count(),
            'successful_scrapes': ScraperLog.objects.filter(status='success').count(),
            'failed_scrapes': ScraperLog.objects.filter(status='failed').count(),
            'avg_processing_time': ScraperLog.objects.filter(
                status='success',
                processing_time__isnull=False
            ).aggregate(Avg('processing_time'))['processing_time__avg'],
            'avg_completeness': ScraperLog.objects.filter(
                status='success',
                data_completeness__isnull=False
            ).aggregate(Avg('data_completeness'))['data_completeness__avg'],
            'last_24h': {
                'total': ScraperLog.objects.filter(started_at__gte=last_24h).count(),
                'successful': ScraperLog.objects.filter(
                    started_at__gte=last_24h,
                    status='success'
                ).count(),
                'failed': ScraperLog.objects.filter(
                    started_at__gte=last_24h,
                    status='failed'
                ).count(),
            },
            'coverage': {
                'total_counties': County.objects.filter(active=True).count(),
                'counties_with_data': County.objects.filter(
                    active=True,
                    tax_data__is_current=True
                ).distinct().count(),
            }
        }

        # Calculate coverage percentage
        if stats['coverage']['total_counties'] > 0:
            stats['coverage']['percentage'] = round(
                (stats['coverage']['counties_with_data'] / stats['coverage']['total_counties']) * 100,
                2
            )
        else:
            stats['coverage']['percentage'] = 0

        return Response(stats)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for User model
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own profile
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user information"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserProfile model
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own profile
        if self.request.user.is_staff:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Get or update current user's profile"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        if request.method == 'GET':
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        else:
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoanEstimateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for LoanEstimate model
    """
    queryset = LoanEstimate.objects.all().select_related(
        'user', 'county', 'county__state', 'tax_data'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['county', 'loan_type', 'property_type', 'is_saved']
    ordering_fields = ['created_at', 'property_value', 'loan_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        # Users can only see their own estimates
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return LoanEstimateListSerializer
        return LoanEstimateSerializer

    def perform_create(self, serializer):
        # Set the user to the current user
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def generate_pdf(self, request, pk=None):
        """Generate PDF export of loan estimate"""
        estimate = self.get_object()

        # TODO: Implement PDF generation
        # For now, return a placeholder response
        return Response({
            "message": "PDF generation not yet implemented",
            "estimate_id": estimate.id
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


class DocTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DocTask model with RBAC and status transitions.

    Borrowers can view their own tasks and update responses.
    Staff/admins can view all tasks and manage them.
    """
    queryset = DocTask.objects.all().select_related(
        'user', 'loan_estimate', 'tradeline', 'reviewed_by'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'task_type', 'loan_estimate', 'user']
    ordering_fields = ['created_at', 'due_date', 'status']
    ordering = ['status', 'due_date', '-created_at']

    def get_queryset(self):
        """Filter tasks based on user role."""
        user = self.request.user
        if user.is_staff:
            # Admin/staff can see all tasks
            return self.queryset
        # Borrowers can only see their own tasks
        return self.queryset.filter(user=user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action and user role."""
        if self.action == 'list':
            return DocTaskListSerializer
        elif self.action == 'create':
            return DocTaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            # Staff uses admin serializer, borrowers use update serializer
            if self.request.user.is_staff:
                return DocTaskAdminUpdateSerializer
            return DocTaskUpdateSerializer
        return DocTaskSerializer

    def create(self, request, *args, **kwargs):
        """Create task and return full serialized response."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()

        # Log audit event
        self._log_audit_event(
            event_type='doc_task_created',
            task=task,
            context={'task_type': task.task_type, 'title': task.title}
        )

        # Return full task details using DocTaskSerializer
        return Response(
            DocTaskSerializer(task).data,
            status=status.HTTP_201_CREATED
        )

    def perform_update(self, serializer):
        """Update task, handle status transitions, and log audit event."""
        old_status = serializer.instance.status
        task = serializer.save()
        new_status = task.status

        # Set completed_at timestamp if transitioning to completed
        if new_status == 'completed' and old_status != 'completed':
            from django.utils import timezone
            task.completed_at = timezone.now()
            task.save(update_fields=['completed_at'])

        # Log audit event for status transitions
        if old_status != new_status:
            event_type = self._get_transition_event_type(old_status, new_status)
            self._log_audit_event(
                event_type=event_type,
                task=task,
                context={
                    'old_status': old_status,
                    'new_status': new_status,
                    'transitioned_by': self.request.user.username
                }
            )

    def perform_destroy(self, instance):
        """Prevent deletion, only allow cancellation via status update."""
        raise serializers.ValidationError(
            "Cannot delete doc tasks. Use status='cancelled' to cancel tasks."
        )

    @extend_schema(
        summary="Submit task response (borrower action)",
        request=DocTaskUpdateSerializer,
        responses={200: DocTaskSerializer}
    )
    @action(detail=True, methods=['post'], url_path='submit')
    def submit_response(self, request, pk=None):
        """
        Borrower submits their response to a task.
        Transitions status to 'completed' and logs audit event.
        """
        task = self.get_object()

        # Only task owner can submit
        if task.user != request.user:
            return Response(
                {"detail": "You can only submit your own tasks."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate status allows submission
        if task.status not in ['pending', 'in_progress']:
            return Response(
                {"detail": f"Cannot submit task with status '{task.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update task with borrower response
        serializer = DocTaskUpdateSerializer(
            task,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        # Force status to completed
        from django.utils import timezone
        task = serializer.save(
            status='completed',
            completed_at=timezone.now()
        )

        # Log audit event
        self._log_audit_event(
            event_type='doc_task_submitted',
            task=task,
            context={
                'has_notes': bool(task.borrower_notes),
                'document_count': len(task.uploaded_documents or [])
            }
        )

        return Response(DocTaskSerializer(task).data)

    @extend_schema(
        summary="Approve task (admin action)",
        responses={200: DocTaskSerializer}
    )
    @action(detail=True, methods=['post'], url_path='approve', permission_classes=[IsAuthenticated])
    def approve_task(self, request, pk=None):
        """
        Admin approves a completed task.
        Logs audit event.
        """
        if not request.user.is_staff:
            return Response(
                {"detail": "Only staff can approve tasks."},
                status=status.HTTP_403_FORBIDDEN
            )

        task = self.get_object()

        if task.status != 'completed':
            return Response(
                {"detail": "Can only approve completed tasks."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update reviewed_by and admin_notes if provided
        task.reviewed_by = request.user
        if 'admin_notes' in request.data:
            task.admin_notes = request.data['admin_notes']
        task.save(update_fields=['reviewed_by', 'admin_notes'])

        # Log audit event
        self._log_audit_event(
            event_type='doc_task_approved',
            task=task,
            context={'reviewed_by': request.user.username}
        )

        return Response(DocTaskSerializer(task).data)

    @extend_schema(
        summary="Request revision (admin action)",
        request={'application/json': {'type': 'object', 'properties': {'admin_notes': {'type': 'string'}}}},
        responses={200: DocTaskSerializer}
    )
    @action(detail=True, methods=['post'], url_path='request-revision', permission_classes=[IsAuthenticated])
    def request_revision(self, request, pk=None):
        """
        Admin requests revision on a completed task.
        Transitions back to 'in_progress' and logs audit event.
        """
        if not request.user.is_staff:
            return Response(
                {"detail": "Only staff can request revisions."},
                status=status.HTTP_403_FORBIDDEN
            )

        task = self.get_object()

        if task.status != 'completed':
            return Response(
                {"detail": "Can only request revision on completed tasks."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update task status and admin notes
        task.status = 'in_progress'
        task.reviewed_by = request.user
        task.admin_notes = request.data.get('admin_notes', '')
        task.completed_at = None  # Reset completion timestamp
        task.save(update_fields=['status', 'reviewed_by', 'admin_notes', 'completed_at'])

        # Log audit event
        self._log_audit_event(
            event_type='doc_task_revision_requested',
            task=task,
            context={
                'reviewed_by': request.user.username,
                'admin_notes': task.admin_notes[:100]  # First 100 chars
            }
        )

        return Response(DocTaskSerializer(task).data)

    @extend_schema(
        summary="Get tasks summary statistics",
        responses={200: {'type': 'object'}}
    )
    @action(detail=False, methods=['get'], url_path='stats')
    def task_stats(self, request):
        """Get task statistics for current user or all users (staff)."""
        from django.db.models import Count, Q

        queryset = self.get_queryset()

        stats = {
            'total': queryset.count(),
            'by_status': dict(
                queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')
            ),
            'by_type': dict(
                queryset.values('task_type').annotate(count=Count('id')).values_list('task_type', 'count')
            ),
            'overdue': queryset.filter(
                due_date__lt=timezone.now().date(),
                status__in=['pending', 'in_progress']
            ).count(),
        }

        return Response(stats)

    def _log_audit_event(self, event_type, task, context=None):
        """Helper to log audit events for doc task operations."""
        # Map our event types to AuditEvent types or use context
        # For now, we'll use a generic approach with context
        try:
            event_context = {
                'doc_task_id': task.id,
                'task_type': task.task_type,
                'task_status': task.status,
                **(context or {})
            }

            # Create audit event (simplified - using document_view as placeholder)
            AuditEvent.objects.create(
                event_type='document_view',  # Using existing event type
                user=self.request.user if hasattr(self, 'request') else None,
                borrower_name=task.user.get_full_name() or task.user.username,
                loan_estimate=task.loan_estimate,
                ip_address=self._get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:255] if hasattr(self, 'request') else '',
                context=event_context
            )
        except Exception as e:
            # Log error but don't fail the request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit event: {e}")

    def _get_transition_event_type(self, old_status, new_status):
        """Map status transitions to event type strings."""
        transitions = {
            ('pending', 'in_progress'): 'doc_task_started',
            ('in_progress', 'completed'): 'doc_task_completed',
            ('completed', 'in_progress'): 'doc_task_reopened',
            ('pending', 'cancelled'): 'doc_task_cancelled',
            ('in_progress', 'cancelled'): 'doc_task_cancelled',
        }
        return transitions.get((old_status, new_status), 'doc_task_status_changed')

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
