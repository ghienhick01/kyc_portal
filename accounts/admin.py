from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_verified_user', 'created_at']
    list_filter = ['role', 'is_verified_user', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('KYC Info', {'fields': ('role', 'phone_number', 'organization', 'is_verified_user', 'last_login_ip')}),
    )
