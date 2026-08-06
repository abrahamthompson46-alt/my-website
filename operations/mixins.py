from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied


class StaffRequiredMixin(AccessMixin):
    """Restrict access to staff users."""

    permission_denied_message = "Staff access required."

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_staff:
            raise PermissionDenied(self.permission_denied_message)
        return super().dispatch(request, *args, **kwargs)
