from django.contrib.auth.mixins import LoginRequiredMixin


class PortalMixin(LoginRequiredMixin):
    """Base mixin for all customer portal views."""

    login_url = "accounts:login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("breadcrumb_items", self.get_breadcrumb_items())
        return context

    def get_breadcrumb_items(self):
        return [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
        ]


class UserQuerysetMixin:
    """Scope querysets to the authenticated user."""

    user_field = "user"

    def get_queryset(self):
        return super().get_queryset().filter(**{self.user_field: self.request.user})
