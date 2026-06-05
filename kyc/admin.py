from django.contrib import admin
from .models import KYCApplication, KYCDocument, AuditLog


class KYCDocumentInline(admin.TabularInline):
    model = KYCDocument
    extra = 0
    readonly_fields = ['public_id', 'uploaded_at', 'file_size']


@admin.register(KYCApplication)
class KYCApplicationAdmin(admin.ModelAdmin):
    list_display = ['public_id', 'full_name', 'owner', 'status', 'risk_level', 'created_at']
    list_filter = ['status', 'risk_level']
    search_fields = ['full_name', 'owner__username']
    readonly_fields = ['public_id', 'created_at', 'updated_at', 'submitted_at', 'reviewed_at']
    inlines = [KYCDocumentInline]


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ['public_id', 'document_type', 'application', 'verification_status', 'uploaded_at']
    list_filter = ['document_type', 'verification_status']
    readonly_fields = ['public_id', 'uploaded_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'actor', 'action', 'target_type', 'target_id', 'ip_address']
    list_filter = ['action', 'target_type']
    search_fields = ['actor__username', 'description']
    readonly_fields = ['timestamp', 'actor', 'action', 'target_type', 'target_id',
                       'description', 'ip_address', 'user_agent', 'extra_data']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
