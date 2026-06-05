from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Extended user model with KYC-specific roles.
    Database Architect & RBAC Lead domain.
    """
    class Role(models.TextChoices):
        APPLICANT = 'applicant', 'Applicant'
        REVIEWER = 'reviewer', 'KYC Reviewer'
        COMPLIANCE = 'compliance', 'Compliance Officer'
        ADMIN = 'admin', 'Administrator'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.APPLICANT)
    phone_number = models.CharField(max_length=20, blank=True)
    organization = models.CharField(max_length=100, blank=True)
    is_verified_user = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_reviewer(self):
        return self.role in [self.Role.REVIEWER, self.Role.COMPLIANCE, self.Role.ADMIN]

    @property
    def is_compliance_officer(self):
        return self.role in [self.Role.COMPLIANCE, self.Role.ADMIN]

    @property
    def masked_email(self):
        """Field-level masking - API & IAM Engineer domain."""
        if not self.email:
            return ''
        parts = self.email.split('@')
        if len(parts) != 2:
            return self.email
        local = parts[0]
        if len(local) <= 2:
            return f"{'*' * len(local)}@{parts[1]}"
        return f"{local[0]}{'*' * (len(local)-2)}{local[-1]}@{parts[1]}"
