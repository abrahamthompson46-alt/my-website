from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView

from partners.models import PartnerProfile


class PartnerRequiredMixin(LoginRequiredMixin):
    """Restrict access to users with an active partner profile."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        profile = getattr(request.user, "partner_profile", None)
        if profile is None or not profile.is_active:
            raise PermissionDenied("Partner access required.")
        return super().dispatch(request, *args, **kwargs)


class PartnerDashboardView(PartnerRequiredMixin, TemplateView):
    template_name = "partners/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.partner_profile
        context["partner"] = profile
        context["referral_url"] = self.request.build_absolute_uri(
            f"/?ref={profile.referral_code}"
        )
        context["breadcrumb_items"] = [{"label": "Partner Dashboard"}]
        return context
