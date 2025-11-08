"""
Scraper Integration URL Configuration
"""
from django.urls import path
from . import views

app_name = 'scraper'

urlpatterns = [
    # Trigger manual scrape
    path('trigger/<str:state_code>/<str:county_name>/', views.trigger_scrape, name='trigger'),

    # Bulk scraping
    path('bulk/state/<str:state_code>/', views.bulk_scrape_state, name='bulk_state'),

    # Check stale data
    path('check-stale/', views.check_stale, name='check_stale'),
]
