from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from accounts.models import (
    AuditLog,
    EmailVerificationToken,
    Role,
    User,
    UserRole,
    UserSecurityProfile,
    UserSession,
)


class UserSecurityProfileInline(admin.StackedInline):
    model = UserSecurityProfile
    can_delete = False
    fk_name = "user"
    readonly_fields = ("email_verified_at", "password_changed_at", "locked_until")
    fields = (
        "email_verified",
        "email_verified_at",
        "mfa_enabled",
        "mfa_method",
        "failed_login_attempts",
        "locked_until",
        "must_reset_password",
        "password_changed_at",
    )


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 0
    fk_name = "user"
    autocomplete_fields = ("role", "assigned_by")


@admin.register(User)
class CustomUserAdmin(DjangoUserAdmin):
    list_display = ("email", "username", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("email",)
    inlines = [UserSecurityProfileInline, UserRoleInline]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_system", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("permissions",)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "assigned_by", "created_at")
    search_fields = ("user__email", "role__name")
    autocomplete_fields = ("user", "role", "assigned_by")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("event_type", "user", "ip_address", "message", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("user__email", "message", "ip_address")
    readonly_fields = (
        "event_type",
        "user",
        "actor",
        "ip_address",
        "user_agent",
        "request_path",
        "request_method",
        "status_code",
        "message",
        "metadata",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "device_label", "ip_address", "last_seen_at", "is_current", "revoked_at")
    list_filter = ("is_current", "revoked_at")
    search_fields = ("user__email", "ip_address", "device_label")
    readonly_fields = ("session_key", "user_agent", "created_at", "updated_at")


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "expires_at", "used_at", "created_at")
    search_fields = ("user__email",)
    readonly_fields = ("token_hash", "created_at", "updated_at")
