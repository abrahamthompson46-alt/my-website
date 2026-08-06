from django.contrib.auth.decorators import user_passes_test

from accounts.services.rbac import user_has_permission, user_has_role


def role_required(role_slug):
    def decorator(view_func):
        return user_passes_test(lambda user: user_has_role(user, role_slug))(view_func)

    return decorator


def permission_required(perm_codename, app_label="accounts"):
    def decorator(view_func):
        return user_passes_test(lambda user: user_has_permission(user, perm_codename, app_label))(view_func)

    return decorator
