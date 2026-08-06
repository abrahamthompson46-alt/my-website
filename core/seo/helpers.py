from core.seo.context import absolute_url, build_seo_metadata
from core.seo.schema import (
    build_article_schema,
    build_breadcrumb_schema,
    build_faq_schema,
    build_product_schema,
)


def _image_url(request, obj):
    for field_name in ("og_image", "hero_image", "featured_image", "cover_image", "thumbnail"):
        field = getattr(obj, field_name, None)
        if field:
            try:
                return absolute_url(request, field.url)
            except Exception:
                continue
    return ""


def _description(obj):
    for attr in ("meta_description", "excerpt", "short_description", "summary", "description"):
        value = getattr(obj, attr, "")
        if value:
            return str(value)[:320]
    return ""


def _title(obj):
    for attr in ("display_meta_title", "meta_title", "title", "name"):
        value = getattr(obj, attr, "")
        if value:
            return str(value)
    return ""


def seo_for_object(request, obj, *, breadcrumbs=None, og_type="website", extra_schema=None):
    schema = list(extra_schema or [])
    model_name = obj.__class__.__name__.lower()
    if model_name in {"blogpost", "docarticle"}:
        schema.append(build_article_schema(request, obj))
        og_type = "article"
    elif model_name == "product":
        schema.append(build_product_schema(request, obj))
    if breadcrumbs:
        schema.append(build_breadcrumb_schema(request, breadcrumbs))

    return build_seo_metadata(
        request,
        title=_title(obj),
        description=_description(obj),
        canonical_path=obj.get_absolute_url(),
        og_type=og_type,
        og_image=_image_url(request, obj),
        schema_data=schema,
    )


def seo_for_page(request, *, title, description="", canonical_path="", og_type="website", og_image="", breadcrumbs=None, faqs=None):
    schema = []
    if breadcrumbs:
        schema.append(build_breadcrumb_schema(request, breadcrumbs))
    if faqs:
        schema.append(build_faq_schema(faqs))
    return build_seo_metadata(
        request,
        title=title,
        description=description,
        canonical_path=canonical_path or request.path,
        og_type=og_type,
        og_image=og_image,
        schema_data=schema,
    )
