from core.seo.context import absolute_url
from core.seo.helpers import _description, _image_url, _title, seo_for_object, seo_for_page


class SEOContextMixin:
    seo_title: str = ""
    seo_description: str = ""
    seo_og_type: str = "website"
    seo_robots: str = "index, follow"
    seo_canonical_path: str = ""
    seo_og_image: str = ""

    def get_seo_object(self):
        return getattr(self, "object", None)

    def get_seo_title(self) -> str:
        if self.seo_title:
            return self.seo_title
        obj = self.get_seo_object()
        return _title(obj) if obj else ""

    def get_seo_description(self) -> str:
        if self.seo_description:
            return self.seo_description
        obj = self.get_seo_object()
        return _description(obj) if obj else ""

    def get_seo_og_type(self) -> str:
        obj = self.get_seo_object()
        if obj and obj.__class__.__name__.lower() in {"blogpost", "docarticle"}:
            return "article"
        return self.seo_og_type

    def get_seo_canonical_path(self) -> str:
        if self.seo_canonical_path:
            return self.seo_canonical_path
        obj = self.get_seo_object()
        if obj and hasattr(obj, "get_absolute_url"):
            return obj.get_absolute_url()
        return self.request.path

    def get_seo_og_image(self) -> str:
        if self.seo_og_image:
            return absolute_url(self.request, self.seo_og_image)
        obj = self.get_seo_object()
        if obj:
            return _image_url(self.request, obj)
        return ""

    def get_extra_schema(self, context):
        return []

    def build_seo_metadata(self, context):
        obj = self.get_seo_object()
        breadcrumbs = context.get("breadcrumb_items")
        if obj:
            meta = seo_for_object(
                self.request,
                obj,
                breadcrumbs=breadcrumbs,
                og_type=self.get_seo_og_type(),
            )
        else:
            meta = seo_for_page(
                self.request,
                title=self.get_seo_title(),
                description=self.get_seo_description(),
                canonical_path=self.get_seo_canonical_path(),
                og_type=self.get_seo_og_type(),
                og_image=self.get_seo_og_image(),
                breadcrumbs=breadcrumbs,
            )
        if self.seo_robots != "index, follow":
            meta.robots = self.seo_robots
        if obj and not meta.og_image:
            meta.og_image = _image_url(self.request, obj)
        meta.schema_data.extend(self.get_extra_schema(context))
        return meta

    def render_to_response(self, context, **response_kwargs):
        context["seo_meta"] = self.build_seo_metadata(context)
        return super().render_to_response(context, **response_kwargs)
