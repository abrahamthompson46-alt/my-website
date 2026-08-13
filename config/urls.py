"""
Root URL configuration.
Routes are delegated to reusable app url modules.
"""
import re

import config.admin  # noqa: F401 — white-label admin branding

from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import Http404
from django.urls import include, path, re_path
from django.views.static import serve

from core.media_paths import is_private_media_path

from core.sitemaps import BlogPostSitemap, CMSPageSitemap, ProductSitemap, StaticViewSitemap
from core.views import health_check, robots_txt

sitemaps = {
    "static": StaticViewSitemap,
    "products": ProductSitemap,
    "blog": BlogPostSitemap,
    "pages": CMSPageSitemap,
}


def _uses_local_media_storage() -> bool:
    backend = settings.STORAGES.get("default", {}).get("BACKEND", "")
    return "FileSystemStorage" in backend


def _serve_public_media(request, path, document_root=None):
    """Serve only non-sensitive files from local media storage."""
    if is_private_media_path(path):
        raise Http404("Private media is not publicly accessible.")
    return serve(request, path, document_root=document_root)


def _local_media_urlpatterns():
    """Serve public /media/ from disk. Private paths require authenticated views."""
    if not _uses_local_media_storage():
        return []

    prefix = settings.MEDIA_URL.lstrip("/")
    if not prefix:
        return []

    return [
        re_path(
            rf"^{re.escape(prefix)}(?P<path>.*)$",
            _serve_public_media,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]


urlpatterns = _local_media_urlpatterns() + [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    # Public marketing site
    path("", include("website.urls")),
    path("products/", include("products.urls")),
    path("pages/", include("pages.urls")),
    path("blog/", include("blog.urls")),
    path("docs/", include("documentation.urls")),
    path("careers/", include("careers.urls")),
    path("contact/", include("contact.urls")),
    path("support/", include("support.urls")),
    # Authentication
    path("accounts/", include("accounts.urls")),
    # Portals
    path("app/", include("customer_portal.urls")),
    path("app/payments/", include("payments.urls")),
    path("ops/", include("operations.urls")),
    path("control/", include("control_room.urls")),
    path("partners/", include("partners.urls")),
    # Payment webhooks (public, CSRF-exempt)
    path("payments/webhooks/", include("payments.webhook_urls")),
    # CMS & marketing utilities
    path("cms/", include("cms.urls")),
    path("marketing/", include("marketing.urls")),
]

if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

handler404 = "common.views.handler404"
handler500 = "common.views.handler500"
