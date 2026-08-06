from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django.conf import settings
from django.urls import reverse


@dataclass
class SEOMetadata:
    title: str = ""
    description: str = ""
    canonical_url: str = ""
    og_type: str = "website"
    og_image: str = ""
    twitter_card: str = "summary_large_image"
    robots: str = "index, follow"
    locale: str = "en_US"
    schema_data: list[dict[str, Any]] = field(default_factory=list)

    def merge(self, **kwargs) -> SEOMetadata:
        for key, value in kwargs.items():
            if not hasattr(self, key) or value in (None, ""):
                continue
            if key == "schema_data" and value:
                self.schema_data.extend(value)
            else:
                setattr(self, key, value)
        return self


def absolute_url(request, path: str = "") -> str:
    site_url = getattr(settings, "SITE_URL", "").rstrip("/")
    if site_url:
        return f"{site_url}{path}" if path else site_url
    return request.build_absolute_uri(path)


def default_og_image(request) -> str:
    static_path = getattr(settings, "SEO_DEFAULT_OG_IMAGE", "/static/images/og-default.png")
    return absolute_url(request, static_path)


def build_seo_metadata(
    request,
    *,
    title: str = "",
    description: str = "",
    canonical_path: str = "",
    og_type: str = "website",
    og_image: str = "",
    twitter_card: str = "summary_large_image",
    robots: str = "index, follow",
    schema_data: list[dict[str, Any]] | None = None,
) -> SEOMetadata:
    site_name = getattr(settings, "SITE_NAME", "Website")
    default_description = getattr(settings, "SITE_DESCRIPTION", "")
    default_title = getattr(settings, "SITE_DEFAULT_TITLE", site_name)

    resolved_title = title or default_title
    if title and site_name and site_name not in title:
        resolved_title = f"{title} | {site_name}"

    resolved_description = description or default_description
    canonical = absolute_url(request, canonical_path or request.path)
    image = og_image or default_og_image(request)

    return SEOMetadata(
        title=resolved_title,
        description=resolved_description,
        canonical_url=canonical,
        og_type=og_type,
        og_image=image,
        twitter_card=twitter_card,
        robots=robots,
        locale=getattr(settings, "SEO_LOCALE", "en_US"),
        schema_data=list(schema_data or []),
    )


def home_seo(request) -> SEOMetadata:
    from core.seo.schema import build_organization_schema, build_website_schema

    meta = build_seo_metadata(
        request,
        title=getattr(settings, "SITE_DEFAULT_TITLE", ""),
        description=getattr(settings, "SITE_DESCRIPTION", ""),
        canonical_path=reverse("website:home"),
        og_type="website",
    )
    meta.schema_data.extend([build_organization_schema(request), build_website_schema(request)])
    return meta
