"""Base mixin for platform control room views."""

from django.core.exceptions import PermissionDenied

from accounts.services.rbac import (
    user_can_manage_platform_ops,
    user_can_manage_platform_settings,
    user_can_manage_team,
)
from control_room.help import get_page_help
from operations.mixins import StaffRequiredMixin


class ControlRoomMixin(StaffRequiredMixin):
    """Base mixin for platform control room views."""

    help_key: str | None = None

    def get_help_key(self) -> str | None:
        return self.help_key

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault(
            "breadcrumb_items",
            [{"label": "Super Dashboard", "url_name": "control_room:dashboard"}],
        )
        help_key = self.get_help_key()
        if help_key:
            context["page_help"] = get_page_help(help_key)
        context["can_manage_team"] = user_can_manage_team(self.request.user)
        context["can_manage_platform_ops"] = user_can_manage_platform_ops(self.request.user)
        return context


class PlatformOwnerMixin(ControlRoomMixin):
    """Restrict platform email/deploy tools to owners or granted operators."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            if not user_can_manage_platform_ops(request.user):
                raise PermissionDenied("Platform owner access required for this area.")
        return super().dispatch(request, *args, **kwargs)


class PlatformSettingsMixin(ControlRoomMixin):
    """Restrict configuration and destructive content changes to platform owners/admins."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            if not user_can_manage_platform_settings(request.user):
                raise PermissionDenied("Platform owner or admin access required for this area.")
        return super(ControlRoomMixin, self).dispatch(request, *args, **kwargs)


class TeamManagementMixin(ControlRoomMixin):
    """Restrict team/user management to platform owners and admins."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)
        if not user_can_manage_team(request.user):
            raise PermissionDenied("Platform owner or admin access required to manage team members.")
        return super().dispatch(request, *args, **kwargs)
