from __future__ import annotations

from django.conf import settings

from core.seo.context import absolute_url


def _publisher() -> dict:
    site_name = getattr(settings, "SITE_NAME", "Website")
    site_url = getattr(settings, "SITE_URL", "")
    logo = getattr(settings, "SEO_LOGO_URL", "/static/images/logo.png")
    return {
        "@type": "Organization",
        "name": site_name,
        "url": site_url or None,
        "logo": f"{site_url.rstrip('/')}{logo}" if site_url else logo,
    }


def build_organization_schema(request) -> dict:
    site_name = getattr(settings, "SITE_NAME", "Website")
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": site_name,
        "url": absolute_url(request, "/"),
        "logo": absolute_url(request, getattr(settings, "SEO_LOGO_URL", "/static/images/logo.png")),
        "sameAs": getattr(settings, "SEO_SOCIAL_PROFILES", []),
    }


def build_website_schema(request) -> dict:
    site_name = getattr(settings, "SITE_NAME", "Website")
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": site_name,
        "url": absolute_url(request, "/"),
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": absolute_url(request, "/search/?q={search_term_string}"),
            },
            "query-input": "required name=search_term_string",
        },
    }


def build_breadcrumb_schema(request, items: list[dict]) -> dict:
    elements = []
    for index, item in enumerate(items, start=1):
        url = item.get("url") or item.get("absolute_url")
        if not url and item.get("url_name"):
            from django.urls import reverse

            url = absolute_url(request, reverse(item["url_name"], kwargs=item.get("url_kwargs", {})))
        elements.append(
            {
                "@type": "ListItem",
                "position": index,
                "name": item.get("label") or item.get("name", ""),
                "item": url,
            }
        )
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": elements,
    }


def build_product_schema(request, product) -> dict:
    schema = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": product.name,
        "description": product.meta_description or product.short_description or product.description[:300],
        "url": absolute_url(request, product.get_absolute_url()),
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "publisher": _publisher(),
    }
    if getattr(product, "hero_image", None):
        try:
            schema["image"] = absolute_url(request, product.hero_image.url)
        except Exception:
            pass
    return schema


def build_article_schema(request, article) -> dict:
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article.title,
        "description": getattr(article, "meta_description", "") or getattr(article, "excerpt", ""),
        "url": absolute_url(request, article.get_absolute_url()),
        "datePublished": article.published_at.isoformat() if article.published_at else None,
        "dateModified": (
            article.updated_at.isoformat()
            if getattr(article, "updated_at", None)
            else article.published_at.isoformat() if article.published_at else None
        ),
        "publisher": _publisher(),
    }
    author = getattr(article, "author", None)
    if author:
        schema["author"] = {"@type": "Person", "name": str(author)}
    if getattr(article, "featured_image", None):
        try:
            schema["image"] = absolute_url(request, article.featured_image.url)
        except Exception:
            pass
    return {k: v for k, v in schema.items() if v}


def build_faq_schema(faqs: list[dict]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
            }
            for item in faqs
        ],
    }
