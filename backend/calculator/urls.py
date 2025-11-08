"""
Calculator URL Configuration
"""
from django.urls import path
from . import views

app_name = 'calculator'

urlpatterns = [
    # Main calculation endpoint
    path('', views.calculate_loan_estimate, name='calculate'),

    # List user's loan estimates
    path('estimates/', views.list_loan_estimates, name='list_estimates'),

    # Get specific loan estimate
    path('<int:estimate_id>/', views.get_loan_estimate, name='get_estimate'),

    # Delete loan estimate
    path('<int:estimate_id>/delete/', views.delete_loan_estimate, name='delete_estimate'),

    # Recalculate estimate with updated data
    path('<int:estimate_id>/recalculate/', views.recalculate_estimate, name='recalculate'),
]
