"""
Health check view
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import connections
from django.core.cache import cache
import redis


class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Check health of all services"""
        health = {
            'status': 'healthy',
            'services': {}
        }

        # Check database
        try:
            connections['default'].ensure_connection()
            health['services']['database'] = 'healthy'
        except Exception as e:
            health['services']['database'] = f'unhealthy: {str(e)}'
            health['status'] = 'degraded'

        # Check Redis cache
        try:
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                health['services']['cache'] = 'healthy'
            else:
                health['services']['cache'] = 'unhealthy: cache write/read failed'
                health['status'] = 'degraded'
        except Exception as e:
            health['services']['cache'] = f'unhealthy: {str(e)}'
            health['status'] = 'degraded'

        return Response(health)
