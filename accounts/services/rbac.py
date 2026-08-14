from django.contrib.auth.models import Permission

from accounts.models import Role, UserRole


def get_user_roles(user):
    if not user.is_authenticated:
        return Role.objects.none()
    return Role.objects.filter(user_roles__user=user, is_active=True).distinct()


def user_has_role(user, role_slug):
    if user.is_superuser:
        return True
    return get_user_roles(user).filter(slug=role_slug).exists()


def user_can_manage_platform_settings(user):
    """Platform owners/admins may change site configuration and destructive content."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user_has_role(user, "platform-owner") or user_has_role(user, "platform-admin")


def user_can_manage_operations_actions(user):
    """Sensitive operations workflows (payments, ticket status changes)."""
    return user_can_manage_platform_settings(user)


def user_can_manage_team(user):
    """Platform owners/admins and superusers can invite users and manage roles."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user_has_role(user, "platform-owner") or user_has_role(user, "platform-admin")


def user_is_platform_owner(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user_has_role(user, "platform-owner")


def user_can_manage_platform_ops(user):
    """Platform owners, superusers, or users with the override permission."""
    if not user.is_authenticated:
        return False
    if user.is_superuser or user_has_role(user, "platform-owner"):
        return True
    return user_has_permission(user, "manage_platform_operations", app_label="control_room")


def user_has_permission(user, perm_codename, app_label="accounts"):
    if user.is_superuser:
        return True
    if user.has_perm(f"{app_label}.{perm_codename}"):
        return True
    return (
        get_user_roles(user)
        .filter(permissions__content_type__app_label=app_label, permissions__codename=perm_codename)
        .exists()
    )


def sync_user_permissions(user):
    """Rebuild direct user permissions from all active assigned roles."""
    role_perms = Permission.objects.filter(
        enterprise_roles__user_roles__user=user,
        enterprise_roles__is_active=True,
    ).distinct()
    user.user_permissions.set(role_perms)


def assign_role(user, role, assigned_by=None):
    user_role, created = UserRole.objects.get_or_create(
        user=user, role=role, defaults={"assigned_by": assigned_by}
    )
    if created:
        sync_user_permissions(user)
    return user_role, created


def remove_role(user, role):
    deleted, _ = UserRole.objects.filter(user=user, role=role).delete()
    if deleted:
        sync_user_permissions(user)
    return bool(deleted)
