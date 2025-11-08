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
    ScraperLog, UserProfile, LoanEstimate
)
from .serializers import (
    StateSerializer, CountySerializer, CountyDetailSerializer,
    TaxDataSerializer, TaxDataListSerializer,
    MunicipalitySerializer, ScraperLogSerializer,
    UserSerializer, UserRegistrationSerializer,
    UserProfileSerializer, LoanEstimateSerializer,
    LoanEstimateListSerializer
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
