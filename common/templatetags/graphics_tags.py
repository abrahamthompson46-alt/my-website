from django import template
from django.templatetags.static import static

register = template.Library()

ILLUSTRATIONS = {
    "onboarding",
    "security",
    "integrations",
    "support",
    "billing",
    "partners",
    "empty-generic",
    "video-placeholder",
}

PRODUCT_VISUALS = {
    "erp": "images/products/product-erp.svg",
    "churchhub": "images/products/product-churchhub.svg",
    "microfinance": "images/products/product-microfinance.svg",
    "school": "images/products/product-school.svg",
    "hospital": "images/products/product-hospital.svg",
    "hr": "images/products/product-hr.svg",
}

EMPTY_ILLUSTRATIONS = {
    "generic": "empty-generic",
    "tickets": "support",
    "invoices": "billing",
    "subscriptions": "billing",
    "payments": "billing",
    "licenses": "security",
    "notifications": "empty-generic",
    "downloads": "integrations",
    "documentation": "onboarding",
    "products": "integrations",
    "blog": "onboarding",
    "partners": "partners",
}


def _product_visual_path(accent):
    rel = PRODUCT_VISUALS.get(accent, "images/products/product-default.svg")
    return static(rel)


@register.inclusion_tag("components/graphics/illustration.html")
def ui_illustration(name="empty-generic", alt="", extra_class="", lazy=True):
    safe_name = name if name in ILLUSTRATIONS else "empty-generic"
    return {
        "src": static(f"images/illustrations/{safe_name}.svg"),
        "alt": alt,
        "extra_class": extra_class,
        "lazy": lazy,
    }


@register.inclusion_tag("components/graphics/icon_badge.html")
def ui_icon_badge(icon, size="md", variant="primary", extra_class=""):
    return {
        "icon": icon,
        "size": size,
        "variant": variant,
        "extra_class": extra_class,
    }


@register.inclusion_tag("components/graphics/product_visual.html")
def ui_product_visual(product=None, accent="", alt="", extra_class=""):
    resolved_accent = accent or (getattr(product, "accent", "") if product else "")
    name = getattr(product, "name", "Product") if product else "Product"
    return {
        "src": _product_visual_path(resolved_accent),
        "alt": alt or f"{name} preview",
        "accent": resolved_accent or "default",
        "extra_class": extra_class,
    }


@register.inclusion_tag("components/graphics/blog_cover.html")
def ui_blog_cover(post=None, title="", category="", extra_class=""):
    display_title = title or (getattr(post, "title", "") if post else "")
    display_category = category
    if not display_category and post and getattr(post, "category", None):
        display_category = post.category.name
    initial = (display_category or display_title or "B")[:1].upper()
    return {
        "title": display_title,
        "category": display_category,
        "initial": initial,
        "extra_class": extra_class,
    }


@register.inclusion_tag("components/graphics/empty_state.html")
def ui_empty_state(
    illustration="generic",
    title="",
    message="No data available.",
    action_label=None,
    action_url=None,
    action_url_name=None,
    compact=False,
    extra_class="",
):
    from common.templatetags.ui_tags import _resolve_url

    ill_name = EMPTY_ILLUSTRATIONS.get(illustration, illustration)
    if ill_name not in ILLUSTRATIONS:
        ill_name = "empty-generic"
    return {
        "src": static(f"images/illustrations/{ill_name}.svg"),
        "title": title,
        "message": message,
        "action_label": action_label,
        "action_url": _resolve_url(action_url, action_url_name),
        "compact": compact,
        "extra_class": extra_class,
    }


@register.inclusion_tag("components/graphics/hero_dashboard.html")
def ui_hero_dashboard(extra_class=""):
    return {
        "src": static("images/hero/platform-dashboard.svg"),
        "extra_class": extra_class,
    }
