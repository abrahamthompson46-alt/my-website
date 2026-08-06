import json

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.inclusion_tag("includes/seo/head.html", takes_context=True)
def render_seo_head(context):
    request = context.get("request")
    seo_meta = context.get("seo_meta")
    if seo_meta is None and request:
        from core.seo.context import build_seo_metadata

        seo_meta = build_seo_metadata(
            request,
            robots=context.get("default_seo_robots", "index, follow"),
        )
    return {"seo_meta": seo_meta, "request": request}


@register.simple_tag
def schema_json_ld(schema_data):
    if not schema_data:
        return ""
    if isinstance(schema_data, dict):
        schema_data = [schema_data]
    blocks = []
    for item in schema_data:
        if item:
            blocks.append(
                f'<script type="application/ld+json">{json.dumps(item, ensure_ascii=False)}</script>'
            )
    return mark_safe("\n".join(blocks))


@register.simple_tag(takes_context=True)
def optimized_image(context, image_field, *, alt="", css_class="", sizes="(max-width: 768px) 100vw, 800px", loading="lazy", width="", height=""):
    if not image_field:
        return ""
    request = context.get("request")
    try:
        url = image_field.url
    except Exception:
        return ""
    if request:
        src = request.build_absolute_uri(url) if url.startswith("/") else url
    else:
        src = url
    attrs = [
        f'src="{escape(src)}"',
        f'alt="{escape(alt)}"',
        f'loading="{escape(loading)}"',
        'decoding="async"',
    ]
    if css_class:
        attrs.append(f'class="{escape(css_class)}"')
    if width:
        attrs.append(f'width="{escape(str(width))}"')
    if height:
        attrs.append(f'height="{escape(str(height))}"')
    if sizes:
        attrs.append(f'sizes="{escape(sizes)}"')
    return mark_safe(f"<img {' '.join(attrs)}>")


@register.simple_tag
def preload_asset(href, as_type="font", crossorigin=""):
    attrs = [f'rel="preload"', f'href="{escape(href)}"', f'as="{escape(as_type)}"']
    if crossorigin:
        attrs.append(f'crossorigin="{escape(crossorigin)}"')
    return mark_safe(f"<link {' '.join(attrs)}>")


@register.simple_tag
def seo_default_og_image():
    path = getattr(settings, "SEO_DEFAULT_OG_IMAGE", "/static/images/og-default.png")
    if path.startswith("/static/"):
        return static(path.replace("/static/", "", 1))
    return path
