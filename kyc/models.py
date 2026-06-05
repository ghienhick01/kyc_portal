import uuid
from django.db import models
from django.conf import settings


def document_upload_path(instance, filename):
    return f'kyc_documents/{instance.application.owner.id}/{instance.document_type}/{filename}'


class KYCApplication(models.Model):
    """Core KYC application - one per user (applicant)."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Submitted'
        UNDER_REVIEW = 'under_review', 'Under Review'
        ADDITIONAL_INFO = 'additional_info', 'Additional Info Required'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    class RiskLevel(models.TextChoices):
        LOW = 'low', 'Low Risk'
        MEDIUM = 'medium', 'Medium Risk'
        HIGH = 'high', 'High Risk'
        CRITICAL = 'critical', 'Critical'

    # Anti-IDOR: UUID public ID instead of sequential integer
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='kyc_application'
    )
    assigned_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_applications'
    )

    # Personal information
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # Status & Risk
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    risk_level = models.CharField(max_length=10, choices=RiskLevel.choices, default=RiskLevel.LOW)

    # Metadata
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Review notes
    reviewer_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'KYC Application'
        verbose_name_plural = 'KYC Applications'

    def __str__(self):
        return f"KYC-{str(self.public_id)[:8].upper()} | {self.full_name} | {self.get_status_display()}"

    @property
    def status_badge_class(self):
        classes = {
            'draft': 'badge-draft',
            'submitted': 'badge-submitted',
            'under_review': 'badge-review',
            'additional_info': 'badge-info',
            'approved': 'badge-approved',
            'rejected': 'badge-rejected',
        }
        return classes.get(self.status, 'badge-default')

    @property
    def completion_percentage(self):
        fields = [
            self.full_name, self.date_of_birth, self.nationality,
            self.address_line1, self.city, self.country
        ]
        filled = sum(1 for f in fields if f)
        docs = self.documents.count()
        doc_score = min(docs * 20, 40)
        field_score = int((filled / len(fields)) * 60)
        return field_score + doc_score


class KYCDocument(models.Model):
    """Document uploads for KYC verification."""

    class DocumentType(models.TextChoices):
        PASSPORT = 'passport', 'Passport'
        NATIONAL_ID = 'national_id', 'National ID Card'
        DRIVERS_LICENSE = 'drivers_license', "Driver's License"
        UTILITY_BILL = 'utility_bill', 'Utility Bill'
        BANK_STATEMENT = 'bank_statement', 'Bank Statement'
        SELFIE = 'selfie', 'Selfie / Liveness Photo'
        TAX_DOCUMENT = 'tax_document', 'Tax Document'
        OTHER = 'other', 'Other'

    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        VERIFIED = 'verified', 'Verified'
        REJECTED = 'rejected', 'Rejected'
        EXPIRED = 'expired', 'Expired'

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    application = models.ForeignKey(
        KYCApplication, on_delete=models.CASCADE, related_name='documents'
    )
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    file = models.FileField(upload_to=document_upload_path)
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0)  # bytes
    mime_type = models.CharField(max_length=100, blank=True)

    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    expiry_date = models.DateField(null=True, blank=True)
    document_number = models.CharField(max_length=100, blank=True)
    issuing_country = models.CharField(max_length=100, blank=True)

    reviewer_note = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.application.full_name}"

    @property
    def masked_document_number(self):
        """Field-level masking for sensitive document numbers."""
        if not self.document_number:
            return ''
        n = self.document_number
        if len(n) <= 4:
            return '*' * len(n)
        return '*' * (len(n) - 4) + n[-4:]

    @property
    def file_size_display(self):
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        return f"{self.file_size / (1024*1024):.1f} MB"


class AuditLog(models.Model):
    """Immutable audit trail for all KYC actions."""

    class Action(models.TextChoices):
        VIEW = 'view', 'Viewed'
        CREATE = 'create', 'Created'
        UPDATE = 'update', 'Updated'
        SUBMIT = 'submit', 'Submitted'
        APPROVE = 'approve', 'Approved'
        REJECT = 'reject', 'Rejected'
        UPLOAD = 'upload', 'Document Uploaded'
        DOWNLOAD = 'download', 'Document Downloaded'
        DELETE = 'delete', 'Deleted'
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    target_type = models.CharField(max_length=50)  # model name
    target_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.actor} - {self.action} - {self.target_type}"
