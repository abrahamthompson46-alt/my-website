from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

from accounts.models import AuditEventType
from accounts.services.audit import log_audit_event
from accounts.services.rbac import user_has_permission, user_has_role


class PermissionRequiredMixin(AccessMixin):
    permission_required = None
    role_required = None
    permission_denied_message = "You do not have permission to access this resource."

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.role_required and not user_has_role(request.user, self.role_required):
            log_audit_event(
                AuditEventType.PERMISSION_DENIED,
                request=request,
                message=f"Missing role: {self.role_required}",
            )
            raise PermissionDenied(self.permission_denied_message)
        if self.permission_required and not user_has_permission(request.user, self.permission_required):
            log_audit_event(
                AuditEventType.PERMISSION_DENIED,
                request=request,
                message=f"Missing permission: {self.permission_required}",
            )
            raise PermissionDenied(self.permission_denied_message)
        return super().dispatch(request, *args, **kwargs)


class EmailVerifiedRequiredMixin(AccessMixin):
    """Require verified email before accessing protected views."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            profile = getattr(request.user, "security_profile", None)
            if profile and not profile.email_verified and not request.user.is_staff:
                from django.shortcuts import redirect

                return redirect("accounts:verify_email_prompt")
        return super().dispatch(request, *args, **kwargs)
