from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

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

    Notifications also include personal (organization=null) rows for the user,
    so platform-owner alerts remain visible in the portal.
    """

    user_field = "user"
    organization_field = "organization"
    include_personal_null_org = False

    def get_queryset(self):
        qs = super().get_queryset()
        model = qs.model
        org = getattr(self.request, "organization", None)
        if org is not None and hasattr(model, self.organization_field):
            if self.include_personal_null_org:
                return qs.filter(
                    **{self.user_field: self.request.user}
                ).filter(
                    Q(**{self.organization_field: org})
                    | Q(**{f"{self.organization_field}__isnull": True})
                )
            return qs.filter(**{self.organization_field: org})
        return qs.filter(**{self.user_field: self.request.user})
