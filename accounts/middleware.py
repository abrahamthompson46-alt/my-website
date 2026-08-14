from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Apply enterprise security headers including CSP."""

    def process_response(self, request, response):
        csp_parts = []
        for directive, sources in getattr(settings, "SECURITY_CSP", {}).items():
            csp_parts.append(f"{directive} {' '.join(sources)}")

        if csp_parts:
            response["Content-Security-Policy"] = "; ".join(csp_parts)

        response.setdefault("Referrer-Policy", getattr(settings, "SECURE_REFERRER_POLICY", "strict-origin-when-cross-origin"))
        response.setdefault("Permissions-Policy", getattr(settings, "SECURITY_PERMISSIONS_POLICY", "camera=(), microphone=(), geolocation=()"))
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("X-Frame-Options", getattr(settings, "X_FRAME_OPTIONS", "DENY"))
        return response


class SessionActivityMiddleware(MiddlewareMixin):
    """Update tracked session activity for authenticated users."""

    def process_request(self, request):
        if request.user.is_authenticated and request.session.session_key:
            from accounts.services.sessions import touch_user_session

            touch_user_session(request)


STAFF_PROTECTED_PREFIXES = ("/admin/", "/control/", "/ops/")
MFA_EXEMPT_PREFIXES = (
    "/accounts/login",
    "/accounts/logout",
    "/accounts/logged-out",
    "/accounts/mfa/",
    "/accounts/invite/",
    "/accounts/password-reset",
    "/accounts/verify-email",
    "/static/",
    "/media/",
    "/health/",
)


class StaffMFARequiredMiddleware(MiddlewareMixin):
    """Require MFA for all authenticated staff before using the platform."""

    def process_request(self, request):
        if not (request.user.is_authenticated and request.user.is_staff):
            return None

        path = request.path
        if any(path.startswith(prefix) for prefix in MFA_EXEMPT_PREFIXES):
            return None

        from django.urls import reverse

        from accounts.services.email import get_or_create_security_profile

        profile = get_or_create_security_profile(request.user)
        if profile.mfa_enabled:
            return None

        messages.warning(
            request,
            "Staff accounts must enable two-factor authentication before using the platform.",
        )
        return redirect(reverse("accounts:mfa_enroll"))
