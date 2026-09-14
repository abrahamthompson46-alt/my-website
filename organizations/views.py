from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View

from customer_portal.mixins import PortalMixin
from organizations.models import Organization
from organizations.services import set_active_organization


class OrganizationSwitchView(PortalMixin, View):
    """Switch the active organization for the current session."""

    def post(self, request):
        organization = get_object_or_404(
            Organization,
            pk=request.POST.get("organization_id"),
        )
        if set_active_organization(request, organization):
            messages.success(request, f"Switched to {organization.name}.")
        else:
            messages.error(request, "You do not have access to that organization.")
        next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
        if not next_url:
            next_url = reverse("customer_portal:dashboard")
        return redirect(next_url)
