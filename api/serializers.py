from rest_framework import serializers
from kyc.models import KYCApplication, KYCDocument, AuditLog
from accounts.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """API & IAM Engineer: JWT-protected serializer with field masking."""
    masked_email = serializers.ReadOnlyField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'masked_email', 'role', 'is_verified_user', 'created_at']
        read_only_fields = ['id', 'masked_email', 'is_verified_user', 'created_at']


class KYCDocumentSerializer(serializers.ModelSerializer):
    masked_document_number = serializers.ReadOnlyField()
    file_size_display = serializers.ReadOnlyField()
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)

    class Meta:
        model = KYCDocument
        fields = [
            'public_id', 'document_type', 'document_type_display',
            'masked_document_number', 'issuing_country', 'expiry_date',
            'verification_status', 'verification_status_display',
            'file_size_display', 'uploaded_at'
        ]
        read_only_fields = ['public_id', 'uploaded_at']


class KYCApplicationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    document_count = serializers.IntegerField(source='documents.count', read_only=True)

    class Meta:
        model = KYCApplication
        fields = [
            'public_id', 'full_name', 'status', 'status_display',
            'risk_level', 'risk_level_display', 'owner_username',
            'document_count', 'submitted_at', 'created_at'
        ]


class KYCApplicationDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail view - includes masked fields."""
    owner = UserSerializer(read_only=True)
    documents = KYCDocumentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    completion_percentage = serializers.ReadOnlyField()

    class Meta:
        model = KYCApplication
        fields = [
            'public_id', 'full_name', 'date_of_birth', 'nationality',
            'address_line1', 'address_line2', 'city', 'country', 'postal_code',
            'status', 'status_display', 'risk_level', 'risk_level_display',
            'owner', 'documents', 'reviewer_notes', 'rejection_reason',
            'completion_percentage', 'submitted_at', 'reviewed_at', 'created_at'
        ]
        read_only_fields = ['public_id', 'owner', 'created_at', 'submitted_at']


class AuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'actor_username', 'action', 'action_display',
            'target_type', 'target_id', 'description',
            'ip_address', 'timestamp'
        ]
