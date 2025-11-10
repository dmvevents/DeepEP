"""
Health check and metrics views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.db import connections
from django.core.cache import cache
from django.conf import settings
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


class MetricsView(APIView):
    """
    Metrics endpoint for observability (admin only)
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Get current metrics"""
        metrics = {}

        # Get cached metrics
        metric_keys = [
            'api_requests_total',
            'api_errors_4xx',
            'api_errors_5xx',
            'api_exceptions',
            'llm_tokens_today',
        ]

        for key in metric_keys:
            cache_key = f'metrics:{key}'
            value = cache.get(cache_key, 0)
            metrics[key] = value

        # Add rate limit info
        daily_limit = getattr(settings, 'LLM_DAILY_TOKEN_LIMIT', 100000)
        llm_usage = metrics.get('llm_tokens_today', 0)
        metrics['llm_token_usage_percent'] = round((llm_usage / daily_limit * 100), 2) if daily_limit > 0 else 0
        metrics['llm_daily_limit'] = daily_limit

        # Calculate error rate
        total = metrics.get('api_requests_total', 0)
        errors = metrics.get('api_errors_5xx', 0)
        metrics['error_rate_percent'] = round((errors / total * 100), 2) if total > 0 else 0

        return Response(metrics)
