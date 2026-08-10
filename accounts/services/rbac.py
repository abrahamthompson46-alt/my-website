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


def user_can_manage_team(user):
    """Platform owners/admins and superusers can invite users and manage roles."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user_has_role(user, "platform-owner") or user_has_role(user, "platform-admin")


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
