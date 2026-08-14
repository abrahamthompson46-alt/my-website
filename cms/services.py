"""CMS page loading utilities."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from cms.models import (
    CMSDownload,
    CMSPage,
    FAQ,
    HeroBanner,
    HeroPlacement,
    NewsArticle,
    PageType,
    TeamMember,
    Testimonial,
)


def get_published_page(slug):
    return get_object_or_404(CMSPage, slug=slug, is_published=True)


def get_home_page():
    page = CMSPage.objects.filter(page_type=PageType.HOME, is_published=True).first()
    if not page:
        return None
    return build_page_context(page)


def get_about_page():
    page = CMSPage.objects.filter(page_type=PageType.ABOUT, is_published=True).first()
    if not page:
        return None
    return build_page_context(page)


def build_page_context(page):
    """Build template-friendly context from a CMS page."""
    sections = {}
    for section in page.sections.filter(is_active=True).prefetch_related("items"):
        sections[section.section_key] = {
            "section": section,
            "items": list(section.items.filter(is_active=True)),
        }

    hero = page.hero if page.hero and page.hero.is_active else None

    return {
        "page": page,
        "hero": hero,
        "sections": sections,
    }


def get_section(page_context, key, default=None):
    if not page_context:
        return default
    return page_context.get("sections", {}).get(key, default)


def section_header(page_context, key):
    data = get_section(page_context, key)
    return data["section"] if data else None


def section_items(page_context, key):
    data = get_section(page_context, key)
    return data["items"] if data else []


def get_home_testimonials(limit=3):
    return list(
        Testimonial.objects.filter(is_published=True, show_on_home=True).order_by("sort_order")[:limit]
    )


def get_home_news(limit=3):
    from marketing.models import BlogPost

    articles = list(
        NewsArticle.objects.filter(is_published=True).order_by("-published_at", "-created_at")[:limit]
    )
    if articles:
        from website.services.homepage import filter_home_news

        return filter_home_news(articles)
    posts = list(
        BlogPost.objects.filter(is_published=True).order_by("-published_at", "-created_at")[: limit * 2]
    )
    from website.services.homepage import filter_home_news

    return filter_home_news(posts)[:limit]


def get_about_team():
    return TeamMember.objects.filter(is_published=True, show_on_about=True).order_by("sort_order")


def get_published_faqs(product=None):
    qs = FAQ.objects.filter(is_published=True).select_related("category")
    if product:
        qs = qs.filter(Q(product=product) | Q(product__isnull=True))
    return qs.order_by("category__sort_order", "sort_order")


def get_product_hero(product):
    return (
        HeroBanner.objects.filter(
            is_active=True,
            linked_product=product,
            placement=HeroPlacement.PRODUCT,
        ).first()
        or HeroBanner.objects.filter(
            is_active=True,
            linked_product=product,
        ).first()
    )


def get_published_downloads(product=None):
    qs = CMSDownload.objects.filter(is_published=True)
    if product:
        qs = qs.filter(Q(product=product) | Q(product__isnull=True))
    return qs.order_by("sort_order", "title")


def build_home_context():
    """Merge CMS home page data with static fallbacks."""
    from website.content import get_homepage_context

    fallback = get_homepage_context()
    page_ctx = get_home_page()

    if not page_ctx:
        return fallback

    sections = page_ctx["sections"]
    hero_banner = page_ctx.get("hero")

    if hero_banner:
        hero = {
            "eyebrow": hero_banner.eyebrow,
            "headline": hero_banner.headline,
            "subheadline": hero_banner.subheadline,
            "trust_text": hero_banner.trust_text,
            "cta_primary_label": hero_banner.cta_primary_label or "Explore products",
            "cta_primary_url": hero_banner.cta_primary_url or "",
            "cta_secondary_label": hero_banner.cta_secondary_label or "Request a Demo",
            "cta_secondary_url": hero_banner.cta_secondary_url or "#request-demo",
            "headline_line1": fallback["hero"].get("headline_line1"),
            "headline_line2": fallback["hero"].get("headline_line2"),
            "product_pills": fallback["hero"].get("product_pills"),
        }
    else:
        hero = fallback["hero"]

    def items_for(key, fallback_key=None):
        sec = sections.get(key)
        if sec and sec["items"]:
            return sec["items"]
        return fallback.get(fallback_key or key, [])

    def header_for(key):
        sec = sections.get(key)
        return sec["section"] if sec else None

    testimonials = get_home_testimonials()
    if not testimonials:
        testimonials = fallback["testimonials"]

    latest_news = get_home_news()
    if not latest_news:
        latest_news = fallback["latest_news"]

    from website.services.homepage import (
        get_trust_signals,
        should_show_home_news,
        should_show_home_testimonials,
    )

    trust_items = items_for("trust_signals", "trust_signals")
    if trust_items and hasattr(trust_items[0], "title"):
        trust_signals = [
            {
                "icon": item.icon or "check-circle",
                "title": item.title,
                "description": item.description,
            }
            for item in trust_items
        ]
    else:
        trust_signals = get_trust_signals(fallback.get("trust_signals"))

    def header_or_fallback(key, fallback_key):
        return header_for(key) or fallback.get(fallback_key, {})

    return {
        "cms_page": page_ctx["page"],
        "hero": hero,
        "hero_banner": hero_banner,
        "trust_strip": fallback.get("trust_strip", []),
        "featured_products_section": header_for("featured_products"),
        "why_choose_us_section": header_for("why_choose_us"),
        "why_choose_us": items_for("why_choose_us"),
        "industries_section": header_for("industries"),
        "industries": items_for("industries"),
        "testimonials_section": header_for("testimonials"),
        "testimonials": testimonials,
        "show_testimonials": should_show_home_testimonials(testimonials),
        "latest_news_section": header_for("latest_news"),
        "latest_news": latest_news,
        "show_latest_news": should_show_home_news(latest_news),
        "statistics_section": header_for("statistics"),
        "statistics": items_for("statistics"),
        "cta_section": header_or_fallback("cta", "cta_section"),
        "request_demo_section": header_or_fallback("request_demo", "request_demo_section"),
        "demo_benefits": items_for("request_demo"),
        "newsletter_section": header_or_fallback("newsletter", "newsletter_section"),
        "trust_signals": trust_signals,
        "trust_signals_section": header_for("trust_signals"),
    }


def build_about_context():
    """Build about page context from CMS with fallbacks."""
    page_ctx = get_about_page()
    if not page_ctx:
        return {
            "cms_page": None,
            "hero": None,
            "sections": {},
            "team_members": get_about_team(),
        }

    return {
        "cms_page": page_ctx["page"],
        "hero": page_ctx.get("hero"),
        "sections": page_ctx["sections"],
        "team_members": get_about_team(),
    }
