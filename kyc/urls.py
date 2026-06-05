from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('application/new/', views.application_create, name='application_create'),
    path('application/<uuid:public_id>/', views.application_detail, name='application_detail'),
    path('application/<uuid:public_id>/edit/', views.application_edit, name='application_edit'),
    path('application/<uuid:public_id>/submit/', views.application_submit, name='application_submit'),
    path('application/<uuid:public_id>/upload/', views.document_upload, name='document_upload'),
    path('application/<uuid:public_id>/review/', views.review_application, name='review_application'),
    path('document/<uuid:doc_public_id>/delete/', views.document_delete, name='document_delete'),
    path('audit-log/', views.audit_log_view, name='audit_log'),
]
