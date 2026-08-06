from django.views.generic import DetailView, ListView, TemplateView

from core.seo.mixins import SEOContextMixin
from documentation.constants import SECTIONS
from documentation.models import DocAPIEndpoint, DocArticle, DocCategory, DocDownload, DocVideo
from documentation.services import (
    get_api_endpoints,
    get_articles,
    get_downloads,
    get_published_categories,
    get_section_by_slug,
    get_videos,
    resolve_product,
    search_documentation,
)


class DocsContextMixin(SEOContextMixin):
    """Shared documentation layout context."""

    def get_product(self):
        return resolve_product(self.request.GET.get("product"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_product()
        context["doc_product"] = product
        context["doc_categories"] = get_published_categories(product)
        context["doc_sections"] = SECTIONS
        context["doc_search_query"] = self.request.GET.get("q", "")
        return context


class DocumentationIndexView(DocsContextMixin, TemplateView):
    template_name = "documentation/index.html"
    seo_title = "Documentation"
    seo_description = "Product documentation, guides, API references, and downloads."
    seo_og_image = "/static/images/og/docs.svg"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_product()
        context["featured_articles"] = get_articles(product=product, featured_only=True)[:6]
        context["getting_started"] = get_articles(article_type="getting_started", product=product)[:4]
        context["breadcrumb_items"] = [{"label": "Documentation"}]
        return context


class DocumentationSearchView(DocsContextMixin, TemplateView):
    template_name = "documentation/search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()
        context["query"] = query
        context["results"] = search_documentation(query, product=self.get_product())
        context["result_count"] = sum(len(v) for v in context["results"].values())
        context["breadcrumb_items"] = [
            {"label": "Documentation", "url_name": "documentation:index"},
            {"label": "Search"},
        ]
        return context


class CategoryListView(DocsContextMixin, ListView):
    model = DocCategory
    template_name = "documentation/categories.html"
    context_object_name = "categories"

    def get_queryset(self):
        return get_published_categories(self.get_product())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Documentation", "url_name": "documentation:index"},
            {"label": "Categories"},
        ]
        return context


class CategoryDetailView(DocsContextMixin, DetailView):
    model = DocCategory
    template_name = "documentation/category.html"
    context_object_name = "category"
    slug_field = "slug"

    def get_queryset(self):
        return get_published_categories(self.get_product())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object
        context["articles"] = category.articles.filter(is_published=True).order_by("sort_order")
        context["videos"] = category.videos.filter(is_published=True).order_by("sort_order")
        context["downloads"] = category.downloads.filter(is_published=True).order_by("sort_order")
        context["api_endpoints"] = category.api_endpoints.filter(is_published=True).order_by("sort_order")
        context["breadcrumb_items"] = [
            {"label": "Documentation", "url_name": "documentation:index"},
            {"label": "Categories", "url_name": "documentation:categories"},
            {"label": category.name},
        ]
        return context


class ArticleDetailView(DocsContextMixin, DetailView):
    model = DocArticle
    template_name = "documentation/article.html"
    context_object_name = "article"
    slug_field = "slug"

    def get_queryset(self):
        return DocArticle.objects.filter(is_published=True).select_related("category", "product")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object
        context["related_articles"] = (
            DocArticle.objects.filter(is_published=True, category=article.category)
            .exclude(pk=article.pk)
            .order_by("sort_order")[:5]
        )
        crumbs = [{"label": "Documentation", "url_name": "documentation:index"}]
        if article.category:
            crumbs.append({"label": article.category.name, "url": article.category.get_absolute_url()})
        crumbs.append({"label": article.title})
        context["breadcrumb_items"] = crumbs
        return context


class SectionArticleListView(DocsContextMixin, ListView):
    template_name = "documentation/section.html"
    context_object_name = "articles"

    def get_section(self):
        return get_section_by_slug(self.kwargs["section_slug"])

    def get_queryset(self):
        section = self.get_section()
        if not section or not section.get("type"):
            return DocArticle.objects.none()
        return get_articles(article_type=section["type"], product=self.get_product())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section = self.get_section()
        context["section"] = section
        context["breadcrumb_items"] = [
            {"label": "Documentation", "url_name": "documentation:index"},
            {"label": section["label"] if section else "Section"},
        ]
        return context


class VideoListView(DocsContextMixin, ListView):
    model = DocVideo
    template_name = "documentation/videos.html"
    context_object_name = "videos"

    def get_queryset(self):
        return get_videos(self.get_product())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Documentation", "url_name": "documentation:index"},
            {"label": "Videos"},
        ]
        return context


class DownloadListView(DocsContextMixin, ListView):
    model = DocDownload
    template_name = "documentation/downloads.html"
    context_object_name = "downloads"

    def get_queryset(self):
        return get_downloads(self.get_product())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Documentation", "url_name": "documentation:index"},
            {"label": "Downloads"},
        ]
        return context


class APIListView(DocsContextMixin, ListView):
    model = DocAPIEndpoint
    template_name = "documentation/api.html"
    context_object_name = "endpoints"

    def get_queryset(self):
        return get_api_endpoints(self.get_product())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        endpoints = context["endpoints"]
        grouped = {}
        for endpoint in endpoints:
            group = endpoint.category.name if endpoint.category else "General"
            grouped.setdefault(group, []).append(endpoint)
        context["endpoint_groups"] = grouped
        context["api_articles"] = get_articles(article_type="api", product=self.get_product())
        context["breadcrumb_items"] = [
            {"label": "Documentation", "url_name": "documentation:index"},
            {"label": "API Documentation"},
        ]
        return context
