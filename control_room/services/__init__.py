"""Control room services."""

from __future__ import annotations

from django.conf import settings as django_settings
from django.core.cache import cache
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from common import navigation as nav_constants
from control_room.models import FeatureFlag, NavigationMenu, PlatformSettings, SiteAnnouncement
from control_room.validators import favicon_mime_type

CACHE_TTL = 300
SETTINGS_CACHE_KEY = "control_room:platform_settings"
NAV_CACHE_PREFIX = "control_room:nav:"


def get_platform_settings() -> PlatformSettings:
    cached = cache.get(SETTINGS_CACHE_KEY)
    if cached:
        return cached
    settings_obj = PlatformSettings.load()
    cache.set(SETTINGS_CACHE_KEY, settings_obj, CACHE_TTL)
    return settings_obj


def invalidate_platform_settings_cache():
    cache.delete(SETTINGS_CACHE_KEY)


def get_site_context() -> dict:
    """Merged site metadata for templates (DB overrides env defaults)."""
    ps = get_platform_settings()
    from control_room.services.theme import get_brand_colors, get_brand_theme_css

    brand = get_brand_colors(ps)
    context = {
        "SITE_NAME": ps.site_name or django_settings.SITE_NAME,
        "SITE_URL": django_settings.SITE_URL,
        "SITE_DESCRIPTION": ps.site_description or getattr(django_settings, "SITE_DESCRIPTION", ""),
        "SITE_DEFAULT_TITLE": ps.default_seo_title or ps.site_name,
        "SITE_TAGLINE": ps.site_tagline,
        "SEO_TWITTER_HANDLE": ps.seo_twitter_handle or getattr(django_settings, "SEO_TWITTER_HANDLE", ""),
        "SEO_DEFAULT_OG_IMAGE": ps.seo_default_og_image or getattr(
            django_settings, "SEO_DEFAULT_OG_IMAGE", "/static/images/og-default.svg"
        ),
        "FOOTER_COPYRIGHT": ps.footer_copyright,
        "CONTACT_EMAIL": ps.contact_email,
        "SUPPORT_EMAIL": ps.support_email,
        "CONTACT_PHONE": ps.contact_phone,
        "MAINTENANCE_MODE": ps.maintenance_mode,
        "MAINTENANCE_MESSAGE": ps.maintenance_message,
        "HEADER_CTA_PRIMARY_LABEL": ps.header_cta_primary_label,
        "HEADER_CTA_PRIMARY_URL_NAME": ps.header_cta_primary_url_name,
        "HEADER_CTA_SECONDARY_LABEL": ps.header_cta_secondary_label,
        "HEADER_CTA_SECONDARY_URL_NAME": ps.header_cta_secondary_url_name,
        "DEMO_FORM_ENABLED": ps.demo_form_enabled,
        "NEWSLETTER_ENABLED": ps.newsletter_enabled,
        "PARTNER_PROGRAM_ENABLED": ps.partner_program_enabled,
        "PUBLIC_REGISTRATION_ENABLED": ps.public_registration_enabled,
        "SOCIAL_LINKEDIN_URL": ps.social_linkedin_url,
        "SOCIAL_TWITTER_URL": ps.social_twitter_url,
        "SOCIAL_YOUTUBE_URL": ps.social_youtube_url,
        "SUPPORT_SLA_HOURS": ps.support_sla_hours,
        "BRAND_THEME_PRESET": ps.brand_theme_preset,
        "BRAND_PRIMARY_COLOR": brand["primary"],
        "BRAND_ACCENT_COLOR": brand["accent"],
        "BRAND_THEME_COLOR": brand["theme_color"],
        "BRAND_THEME_CSS": get_brand_theme_css(ps),
        "BRAND_LOGO_URL": ps.brand_logo.url if ps.brand_logo else "",
        "BRAND_FAVICON_URL": ps.brand_favicon.url if ps.brand_favicon else "",
        "BRAND_FAVICON_TYPE": favicon_mime_type(ps.brand_favicon.url if ps.brand_favicon else ""),
    }
    return context


def _fallback_nav(code: str):
    fallbacks = {
        "public_header": nav_constants.PUBLIC_HEADER_NAV,
        "public_footer": nav_constants.PUBLIC_FOOTER_COLUMNS,
        "customer_portal": nav_constants.CUSTOMER_PORTAL_NAV,
        "operations": nav_constants.OPERATIONS_NAV,
        "partner_portal": nav_constants.PARTNER_PORTAL_NAV,
        "control_room": nav_constants.CONTROL_ROOM_NAV,
    }
    return fallbacks.get(code, [])


def get_navigation(code: str) -> list:
    cache_key = f"{NAV_CACHE_PREFIX}{code}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    menu = NavigationMenu.objects.filter(code=code, is_active=True).first()
    if menu and menu.structure:
        structure = menu.structure
    else:
        structure = _fallback_nav(code)

    cache.set(cache_key, structure, CACHE_TTL)
    return structure


def invalidate_navigation_cache(code: str | None = None):
    if code:
        cache.delete(f"{NAV_CACHE_PREFIX}{code}")
    else:
        for menu in NavigationMenu.objects.values_list("code", flat=True):
            cache.delete(f"{NAV_CACHE_PREFIX}{menu}")
        for code in (
            "public_header",
            "public_footer",
            "customer_portal",
            "operations",
            "partner_portal",
            "control_room",
        ):
            cache.delete(f"{NAV_CACHE_PREFIX}{code}")


def is_feature_enabled(key: str) -> bool:
    try:
        flag = FeatureFlag.objects.get(key=key)
        return flag.is_enabled
    except FeatureFlag.DoesNotExist:
        return True


def get_active_public_announcements():
    now = timezone.now()
    from django.db.models import Q

    return list(
        SiteAnnouncement.objects.filter(is_active=True, show_on_public=True)
        .filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
        .order_by("sort_order", "-created_at")
    )


def resolve_redirect_target(rule) -> str | None:
    if rule.to_path:
        return rule.to_path
    if rule.to_url_name:
        try:
            return reverse(rule.to_url_name)
        except NoReverseMatch:
            return None
    return None


def get_content_registry() -> list[dict]:
    """Catalog of manageable content domains for the control room hub."""
    from cms.models import CMSPage, FAQ, HeroBanner, Testimonial
    from documentation.models import DocArticle
    from marketing.models import BlogPost
    from products.models import Product, ProductDemoRequest
    from customer_portal.models import SupportTicket

    def _entry(**kwargs):
        admin_model = kwargs.pop("admin_model", None)
        if admin_model:
            app_label, model_name = admin_model.split(".", 1)
            kwargs["admin_url"] = f"/admin/{app_label}/{model_name}/"
        return kwargs

    return [
        _entry(
            key="platform",
            title="Platform settings",
            description="Branding, SEO defaults, contact info, maintenance mode",
            url_name="control_room:settings",
            icon="settings",
            count=1,
        ),
        _entry(
            key="navigation",
            title="Navigation",
            description="Header, footer, and portal menus",
            url_name="control_room:navigation",
            icon="menu",
            count=NavigationMenu.objects.count(),
        ),
        _entry(
            key="cms_pages",
            title="CMS pages",
            description="Homepage, about, and custom landing pages",
            admin_model="cms.cmspage",
            icon="layout-dashboard",
            count=CMSPage.objects.count(),
        ),
        _entry(
            key="heroes",
            title="Hero banners",
            description="Hero content for pages and products",
            admin_model="cms.herobanner",
            count=HeroBanner.objects.count(),
            icon="image",
        ),
        _entry(
            key="products",
            title="Products",
            description="Catalog, pricing, features, and media",
            url_name="control_room:products",
            count=Product.objects.count(),
            icon="package",
        ),
        _entry(
            key="blog",
            title="Blog & marketing",
            description="Posts, events, case studies, resources",
            admin_model="marketing.blogpost",
            count=BlogPost.objects.count(),
            icon="book-open",
        ),
        _entry(
            key="docs",
            title="Documentation",
            description="Articles, categories, API references",
            admin_model="documentation.docarticle",
            count=DocArticle.objects.count(),
            icon="file-check",
        ),
        _entry(
            key="faqs",
            title="FAQs & testimonials",
            description="Support content and social proof",
            count=FAQ.objects.count() + Testimonial.objects.count(),
            icon="help-circle",
        ),
        _entry(
            key="customers",
            title="Customers & support",
            description="Tickets, subscriptions, and portal users",
            url_name="operations:support",
            count=SupportTicket.objects.filter(status__in=["open", "in_progress", "waiting"]).count(),
            icon="life-buoy",
        ),
        _entry(
            key="leads",
            title="Leads & demos",
            description="Newsletter subscribers and demo requests",
            url_name="operations:demo_requests",
            count=ProductDemoRequest.objects.filter(status="new").count(),
            icon="user-plus",
        ),
        _entry(
            key="payments",
            title="Payments & billing",
            description="Transactions, gateways, and manual confirmations",
            url_name="operations:payments",
            icon="credit-card",
        ),
        _entry(
            key="redirects",
            title="URL redirects",
            description="Manage path redirects without deployments",
            url_name="control_room:redirects",
            icon="external-link",
        ),
    ]


def log_control_change(user, area: str, action: str, summary: str, details=None):
    from control_room.models import ControlChangeLog

    ControlChangeLog.objects.create(
        user=user if user and user.is_authenticated else None,
        area=area,
        action=action,
        summary=summary,
        details=details or {},
    )
