"""Base mixin for platform control room views."""

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
        return context
