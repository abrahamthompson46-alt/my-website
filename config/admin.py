"""White-label Django admin with enterprise branding."""

from django.conf import settings
from django.contrib import admin
from django.shortcuts import redirect


def configure_admin_site():
    site_name = getattr(settings, "SITE_NAME", "Enterprise Platform")
    admin.site.site_header = site_name
    admin.site.site_title = site_name
    admin.site.index_title = "Platform Administration"

    original_index = admin.site.index

    def super_dashboard_index(request, extra_context=None):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect("control_room:dashboard")
        return original_index(request, extra_context=extra_context)

    admin.site.index = super_dashboard_index


configure_admin_site()
