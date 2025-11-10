"""
Tenant API views for white-label theming
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from drf_spectacular.utils import extend_schema

from .tenant import Tenant
from .serializers_tenant import TenantSerializer


class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Tenant model (read-only for clients)
    Provides theme configuration for white-label support
    """
    queryset = Tenant.objects.filter(is_active=True)
    serializer_class = TenantSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    @extend_schema(
        summary="Get current tenant theme configuration",
        responses={200: TenantSerializer}
    )
    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Get current tenant theme based on request context.
        Returns default tenant if ENABLE_TENANT_THEMING is False.
        """
        if not settings.ENABLE_TENANT_THEMING:
            # Return default theme when feature flag is disabled
            return Response({
                'name': 'Mortgage Calculator',
                'slug': 'default',
                'logo_url': '',
                'colors': {
                    'primary': '#667eea',
                    'secondary': '#10b981',
                    'accent': '#764ba2',
                },
                'contact': {
                    'email': '',
                    'phone': '',
                    'website': '',
                }
            })

        # In production, determine tenant from:
        # - Subdomain (tenant.yourdomain.com)
        # - Custom domain mapping
        # - User's assigned tenant
        # For now, return first active tenant or default
        tenant = Tenant.objects.filter(is_active=True).first()

        if not tenant:
            return Response({
                'name': 'Mortgage Calculator',
                'slug': 'default',
                'logo_url': '',
                'colors': {
                    'primary': '#667eea',
                    'secondary': '#10b981',
                    'accent': '#764ba2',
                },
                'contact': {
                    'email': '',
                    'phone': '',
                    'website': '',
                }
            })

        serializer = self.get_serializer(tenant)
        return Response(serializer.data)
