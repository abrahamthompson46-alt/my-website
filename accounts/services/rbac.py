from accounts.models import Role, UserRole


def get_user_roles(user):
    if not user.is_authenticated:
        return Role.objects.none()
    return Role.objects.filter(user_roles__user=user, is_active=True).distinct()


def user_has_role(user, role_slug):
    if user.is_superuser:
        return True
    return get_user_roles(user).filter(slug=role_slug).exists()


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


def assign_role(user, role, assigned_by=None):
    user_role, created = UserRole.objects.get_or_create(user=user, role=role, defaults={"assigned_by": assigned_by})
    if created:
        for permission in role.permissions.all():
            user.user_permissions.add(permission)
    return user_role, created


def remove_role(user, role):
    deleted, _ = UserRole.objects.filter(user=user, role=role).delete()
    if deleted:
        for permission in role.permissions.all():
            user.user_permissions.remove(permission)
    return bool(deleted)
