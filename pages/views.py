from django.views.generic import DetailView, TemplateView

from cms.services import build_about_context
from core.seo.mixins import SEOContextMixin


class AboutView(SEOContextMixin, TemplateView):
    template_name = "pages/about.html"
    seo_title = "About"
    seo_description = "Learn about our mission, team, and enterprise platform."
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_about_context())
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "About"},
        ]
        return context


class PageDetailView(SEOContextMixin, DetailView):
    template_name = "pages/detail.html"
    context_object_name = "cms_page"
    slug_field = "slug"

    def get_queryset(self):
        from cms.models import CMSPage

        return CMSPage.objects.filter(is_published=True, page_type="custom")

    def get_context_data(self, **kwargs):
        from cms.services import build_page_context

        context = super().get_context_data(**kwargs)
        page_ctx = build_page_context(self.object)
        context.update(page_ctx)
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": self.object.title},
        ]
        return context


class PageListView(TemplateView):
    template_name = "pages/list.html"

    def get_context_data(self, **kwargs):
        from cms.models import CMSPage, PageType

        context = super().get_context_data(**kwargs)
        context["pages"] = CMSPage.objects.filter(
            is_published=True,
            page_type=PageType.CUSTOM,
        ).order_by("title")
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Pages"},
        ]
        return context
