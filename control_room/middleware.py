from django.shortcuts import redirect
from django.urls import reverse

from control_room.services import resolve_redirect_target


class PlatformRedirectMiddleware:
    """Apply database-configured URL redirects."""

    def __init__(self, get_response):
        self.get_response = get_response
        self._rules = None
        self._loaded_at = 0

    def _get_rules(self):
        import time

        from control_room.models import RedirectRule

        now = time.time()
        if self._rules is None or now - self._loaded_at > 60:
            self._rules = list(RedirectRule.objects.filter(is_active=True))
            self._loaded_at = now
        return self._rules

    def __call__(self, request):
        path = request.path
        if not path.startswith(("/control/", "/admin/", "/static/", "/media/")):
            for rule in self._get_rules():
                if path == rule.from_path or path.rstrip("/") == rule.from_path.rstrip("/"):
                    target = resolve_redirect_target(rule)
                    if target:
                        status = 301 if rule.redirect_type == "301" else 302
                        return redirect(target, permanent=(status == 301))
        return self.get_response(request)


class MaintenanceModeMiddleware:
    """Show maintenance page when enabled in platform settings."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from control_room.services import get_platform_settings

        settings_obj = get_platform_settings()
        if settings_obj.maintenance_mode:
            allowed_prefixes = ("/control/", "/admin/", "/accounts/login", "/static/", "/media/", "/health/")
            if not request.user.is_staff and not request.path.startswith(allowed_prefixes):
                from django.shortcuts import render

                return render(
                    request,
                    "control_room/maintenance.html",
                    {"message": settings_obj.maintenance_message},
                    status=503,
                )
        return self.get_response(request)
