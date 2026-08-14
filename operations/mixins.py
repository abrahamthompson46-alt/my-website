from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

from accounts.services.rbac import user_can_manage_operations_actions


class StaffRequiredMixin(AccessMixin):
    """Restrict access to staff users."""

    permission_denied_message = "Staff access required."

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_staff:
            raise PermissionDenied(self.permission_denied_message)
        return super().dispatch(request, *args, **kwargs)


class OpsActionsMixin(StaffRequiredMixin):
    """Restrict payment, ticket, and demo mutations to platform owners/admins."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            if not user_can_manage_operations_actions(request.user):
                raise PermissionDenied("Platform owner or admin access required for this action.")
        return super().dispatch(request, *args, **kwargs)
