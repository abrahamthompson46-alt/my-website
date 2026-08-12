from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError

from common.navigation import (
    CONTROL_ROOM_NAV,
    CUSTOMER_PORTAL_NAV,
    OPERATIONS_NAV,
    PARTNER_PORTAL_NAV,
    PUBLIC_FOOTER_COLUMNS,
    PUBLIC_HEADER_NAV,
)


def _fallback_site_context(path):
    robots = (
        "noindex, nofollow"
        if path.startswith(("/accounts/", "/app/", "/ops/", "/control/", "/admin/"))
        else "index, follow"
    )
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_URL": settings.SITE_URL,
        "SITE_DESCRIPTION": getattr(settings, "SITE_DESCRIPTION", ""),
        "SITE_DEFAULT_TITLE": getattr(settings, "SITE_DEFAULT_TITLE", settings.SITE_NAME),
        "SITE_TAGLINE": "",
        "SEO_TWITTER_HANDLE": getattr(settings, "SEO_TWITTER_HANDLE", ""),
        "SEO_DEFAULT_OG_IMAGE": getattr(settings, "SEO_DEFAULT_OG_IMAGE", "/static/images/og-default.svg"),
        "FOOTER_COPYRIGHT": "",
        "CONTACT_EMAIL": "",
        "SUPPORT_EMAIL": "",
        "CONTACT_PHONE": "",
        "MAINTENANCE_MODE": False,
        "MAINTENANCE_MESSAGE": "",
        "HEADER_CTA_PRIMARY_LABEL": "Start Free Trial",
        "HEADER_CTA_PRIMARY_URL_NAME": "contact:trial",
        "HEADER_CTA_SECONDARY_LABEL": "Request a Demo",
        "HEADER_CTA_SECONDARY_URL_NAME": "contact:demo",
        "DEMO_FORM_ENABLED": True,
        "NEWSLETTER_ENABLED": True,
        "PARTNER_PROGRAM_ENABLED": True,
        "PUBLIC_REGISTRATION_ENABLED": True,
        "SOCIAL_LINKEDIN_URL": "",
        "SOCIAL_TWITTER_URL": "",
        "SOCIAL_YOUTUBE_URL": "",
        "SUPPORT_SLA_HOURS": 24,
        "BRAND_THEME_PRESET": "zreta_indigo",
        "BRAND_PRIMARY_COLOR": "#1e3a5f",
        "BRAND_ACCENT_COLOR": "#c9a227",
        "BRAND_THEME_COLOR": "#0a1628",
        "BRAND_THEME_CSS": "",
        "BRAND_LOGO_URL": "",
        "BRAND_FAVICON_URL": "",
        "default_seo_robots": robots,
    }


def _load_navigation():
    try:
        from control_room.services import get_navigation

        return get_navigation, True
    except (OperationalError, ProgrammingError, ImportError):
        return None, False


def site_settings(request):
    """Global template context available on every page."""
    path = getattr(request, "path", "")
    try:
        from control_room.services import get_site_context

        context = get_site_context()
    except (OperationalError, ProgrammingError, ImportError):
        context = _fallback_site_context(path)
    else:
        context["default_seo_robots"] = (
            "noindex, nofollow"
            if path.startswith(("/accounts/", "/app/", "/ops/", "/control/", "/admin/"))
            else "index, follow"
        )
    return context


def navigation(request):
    """Inject navigation structures based on current portal context."""
    path = request.path
    get_navigation, db_ready = _load_navigation()

    if db_ready:
        public_header = get_navigation("public_header")
        public_footer = get_navigation("public_footer")
    else:
        public_header = PUBLIC_HEADER_NAV
        public_footer = PUBLIC_FOOTER_COLUMNS

    if path.startswith("/control/"):
        sidebar_nav = get_navigation("control_room") if db_ready else CONTROL_ROOM_NAV
        if request.user.is_authenticated:
            from accounts.services.rbac import user_can_manage_platform_ops

            if not user_can_manage_platform_ops(request.user):
                sidebar_nav = [item for item in sidebar_nav if not item.get("owner_only")]
        portal_type = "control"
    elif path.startswith("/ops/"):
        sidebar_nav = get_navigation("operations") if db_ready else OPERATIONS_NAV
        portal_type = "operations"
    elif path.startswith("/app/"):
        sidebar_nav = get_navigation("customer_portal") if db_ready else CUSTOMER_PORTAL_NAV
        portal_type = "customer"
    elif path.startswith("/partners/"):
        sidebar_nav = get_navigation("partner_portal") if db_ready else PARTNER_PORTAL_NAV
        portal_type = "partner"
    else:
        sidebar_nav = []
        portal_type = None

    unread_notifications = 0
    if portal_type == "customer" and request.user.is_authenticated:
        from customer_portal.models import PortalNotification

        unread_notifications = PortalNotification.objects.filter(
            user=request.user, is_read=False
        ).count()

    return {
        "PUBLIC_HEADER_NAV": public_header,
        "PUBLIC_FOOTER_COLUMNS": public_footer,
        "SIDEBAR_NAV": sidebar_nav,
        "PORTAL_TYPE": portal_type,
        "UNREAD_NOTIFICATIONS": unread_notifications,
    }


def platform_extras(request):
    """Announcements and feature flags for public templates."""
    try:
        from control_room.models import FeatureFlag
        from control_room.services import get_active_public_announcements

        announcements = get_active_public_announcements()
        flags = {flag.key: flag.is_enabled for flag in FeatureFlag.objects.all()}
    except (OperationalError, ProgrammingError, ImportError):
        announcements = []
        flags = {}

    return {
        "SITE_ANNOUNCEMENTS": announcements,
        "FEATURE_FLAGS": flags,
    }
