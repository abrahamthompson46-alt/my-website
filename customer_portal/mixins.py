from django.contrib.auth.mixins import LoginRequiredMixin

from accounts.mixins import EmailVerifiedRequiredMixin


class PortalMixin(EmailVerifiedRequiredMixin, LoginRequiredMixin):
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
    """
    Scope querysets to the active organization when the model is tenant-aware.
    Falls back to the authenticated user for legacy / non-tenant models.
    """

    user_field = "user"
    organization_field = "organization"

    def get_queryset(self):
        qs = super().get_queryset()
        org = getattr(self.request, "organization", None)
        if org is not None and hasattr(qs.model, self.organization_field):
            return qs.filter(**{self.organization_field: org})
        return qs.filter(**{self.user_field: self.request.user})
