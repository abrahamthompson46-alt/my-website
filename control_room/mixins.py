from operations.mixins import StaffRequiredMixin


class ControlRoomMixin(StaffRequiredMixin):
    """Base mixin for platform control room views."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault(
            "breadcrumb_items",
            [{"label": "Super Dashboard", "url_name": "control_room:dashboard"}],
        )
        return context
