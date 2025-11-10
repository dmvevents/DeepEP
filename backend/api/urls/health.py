"""
Health check URL Configuration
"""
from django.urls import path
from ..views_health import HealthCheckView, MetricsView

app_name = 'health'

urlpatterns = [
    path('', HealthCheckView.as_view(), name='health'),
    path('metrics/', MetricsView.as_view(), name='metrics'),
]
