from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # JWT Auth
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Applications
    path('applications/', views.ApplicationListAPI.as_view(), name='api_applications'),
    path('applications/<uuid:public_id>/', views.ApplicationDetailAPI.as_view(), name='api_application_detail'),
    path('applications/stats/', views.ApplicationStatsAPI.as_view(), name='api_stats'),
    # Audit
    path('audit-log/', views.AuditLogAPI.as_view(), name='api_audit_log'),
    # User
    path('me/', views.CurrentUserAPI.as_view(), name='api_me'),
]
