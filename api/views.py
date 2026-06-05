import logging
from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden

from kyc.models import KYCApplication, KYCDocument, AuditLog
from accounts.models import CustomUser
from .serializers import (
    KYCApplicationListSerializer, KYCApplicationDetailSerializer,
    KYCDocumentSerializer, AuditLogSerializer, UserSerializer
)

api_logger = logging.getLogger('kyc.audit')


class IsReviewer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_reviewer


class IsOwnerOrReviewer(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_reviewer:
            return True
        return obj.owner == request.user


# ─── JWT Token Views ────────────────────────────────────────────────────────

class CustomTokenObtainPairView(TokenObtainPairView):
    """Extended JWT login endpoint."""
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            api_logger.info(f"JWT token issued for user: {request.data.get('username')} | IP: {request.META.get('REMOTE_ADDR')}")
        return response


# ─── Application API ────────────────────────────────────────────────────────

class ApplicationListAPI(generics.ListAPIView):
    """List KYC applications - Anti-IDOR filtered by ownership."""
    serializer_class = KYCApplicationListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'owner__username']
    ordering_fields = ['created_at', 'status', 'risk_level']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_reviewer:
            qs = KYCApplication.objects.select_related('owner').all()
            status_param = self.request.query_params.get('status')
            risk_param = self.request.query_params.get('risk')
            if status_param:
                qs = qs.filter(status=status_param)
            if risk_param:
                qs = qs.filter(risk_level=risk_param)
            return qs
        # Applicants only see their own (Anti-IDOR)
        return KYCApplication.objects.filter(owner=self.request.user)


class ApplicationDetailAPI(generics.RetrieveAPIView):
    """Retrieve application detail - enforces Anti-IDOR."""
    serializer_class = KYCApplicationDetailSerializer
    lookup_field = 'public_id'
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReviewer]

    def get_queryset(self):
        return KYCApplication.objects.select_related('owner').prefetch_related('documents')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        api_logger.info(
            f"API | User={request.user.username} viewed application {kwargs.get('public_id')}"
        )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ApplicationStatsAPI(APIView):
    """Dashboard statistics endpoint."""
    permission_classes = [permissions.IsAuthenticated, IsReviewer]

    def get(self, request):
        stats = {
            'total': KYCApplication.objects.count(),
            'by_status': {},
            'by_risk': {},
        }
        for status_val, _ in KYCApplication.Status.choices:
            stats['by_status'][status_val] = KYCApplication.objects.filter(status=status_val).count()
        for risk_val, _ in KYCApplication.RiskLevel.choices:
            stats['by_risk'][risk_val] = KYCApplication.objects.filter(risk_level=risk_val).count()

        return Response(stats)


class AuditLogAPI(generics.ListAPIView):
    """Audit log API - compliance officers only."""
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_compliance_officer:
            return AuditLog.objects.none()
        return AuditLog.objects.select_related('actor').all()[:100]


class CurrentUserAPI(APIView):
    """Current authenticated user info."""
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
