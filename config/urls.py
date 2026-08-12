"""
Root URL configuration.
Routes are delegated to reusable app url modules.
"""
import config.admin  # noqa: F401 — white-label admin branding

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

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


urlpatterns = [
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
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
elif _uses_local_media_storage():
    # Fallback when nginx does not serve /media/ (common after cutover). Prefer nginx in production.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "common.views.handler404"
handler500 = "common.views.handler500"
