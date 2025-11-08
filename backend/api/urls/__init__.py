"""
API URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views import (
    StateViewSet, CountyViewSet, TaxDataViewSet,
    MunicipalityViewSet, ScraperLogViewSet,
    UserViewSet, UserProfileViewSet, LoanEstimateViewSet
)

app_name = 'api'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'states', StateViewSet, basename='state')
router.register(r'counties', CountyViewSet, basename='county')
router.register(r'tax-data', TaxDataViewSet, basename='taxdata')
router.register(r'municipalities', MunicipalityViewSet, basename='municipality')
router.register(r'scraper-logs', ScraperLogViewSet, basename='scraperlog')
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', UserProfileViewSet, basename='userprofile')
router.register(r'loan-estimates', LoanEstimateViewSet, basename='loanestimate')

urlpatterns = [
    path('', include(router.urls)),
]
