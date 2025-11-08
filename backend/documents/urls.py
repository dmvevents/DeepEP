"""
Documents URL Configuration
"""
from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('upload/', views.upload_document, name='upload'),
    path('<int:document_id>/', views.get_document, name='get'),
    path('<int:document_id>/extract/', views.trigger_extraction, name='extract'),
    path('', views.list_documents, name='list'),
]
