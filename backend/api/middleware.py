"""
Observability middleware for error tracking and metrics.
"""
import logging
import time
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class ErrorTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track errors and basic metrics.
    Integrates with Sentry when configured.
    """

    def process_request(self, request):
        """Track request start time"""
        request._start_time = time.time()

    def process_response(self, request, response):
        """Track response time and log errors"""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time

            # Log slow requests (>2s)
            if duration > 2.0:
                logger.warning(
                    f"Slow request: {request.method} {request.path} took {duration:.2f}s"
                )

            # Increment metrics counter
            self._increment_metric('api_requests_total')

            # Track error responses
            if response.status_code >= 500:
                logger.error(
                    f"Server error: {request.method} {request.path} "
                    f"returned {response.status_code} in {duration:.2f}s"
                )
                self._increment_metric('api_errors_5xx')
            elif response.status_code >= 400:
                self._increment_metric('api_errors_4xx')

        return response

    def process_exception(self, request, exception):
        """Log unhandled exceptions"""
        logger.error(
            f"Unhandled exception: {request.method} {request.path}",
            exc_info=exception,
            extra={
                'user_id': getattr(request.user, 'id', None),
                'path': request.path,
                'method': request.method,
            }
        )
        self._increment_metric('api_exceptions')
        return None  # Let Django handle the exception

    def _increment_metric(self, key: str, amount: int = 1):
        """Increment a metric counter in cache"""
        try:
            cache_key = f'metrics:{key}'
            current = cache.get(cache_key, 0)
            cache.set(cache_key, current + amount, timeout=3600)  # 1 hour TTL
        except Exception as e:
            # Don't fail requests due to metrics
            logger.debug(f"Failed to increment metric {key}: {e}")


class LLMRateLimitMiddleware(MiddlewareMixin):
    """
    Middleware to track and enforce LLM API rate limits.
    Guards against cost overruns and cascading failures.
    """

    def process_request(self, request):
        """Check if we're approaching rate limits"""
        # Only check for scraper-related endpoints
        if '/api/scraper/' in request.path or '/scrape' in request.path:
            daily_limit = getattr(settings, 'LLM_DAILY_TOKEN_LIMIT', 100000)

            # Check current usage
            usage_key = 'llm_tokens_today'
            current_usage = cache.get(usage_key, 0)

            # Warn at 80% threshold
            if current_usage >= daily_limit * 0.8:
                logger.warning(
                    f"LLM token usage at {current_usage}/{daily_limit} "
                    f"({current_usage/daily_limit*100:.1f}%)"
                )

                # Block at 100% threshold (safety)
                if current_usage >= daily_limit:
                    logger.error(f"LLM daily token limit exceeded: {current_usage}/{daily_limit}")
                    from django.http import JsonResponse
                    return JsonResponse(
                        {
                            'error': 'Daily LLM token limit exceeded',
                            'detail': 'Service temporarily unavailable. Contact support.',
                        },
                        status=503
                    )

    def process_response(self, request, response):
        """Track LLM token usage from response headers or body"""
        # Implementation note: Token tracking is done in scraper service
        # This middleware monitors the aggregated totals
        return response
