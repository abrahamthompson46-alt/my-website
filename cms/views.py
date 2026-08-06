from django.views.generic import DetailView, ListView

from cms.models import CMSDownload, NewsArticle
from cms.services import get_published_downloads, get_published_faqs


class NewsListView(ListView):
    model = NewsArticle
    template_name = "cms/news_list.html"
    context_object_name = "articles"
    paginate_by = 10

    def get_queryset(self):
        return NewsArticle.objects.filter(is_published=True).order_by("-published_at", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "News"},
        ]
        return context


class NewsDetailView(DetailView):
    model = NewsArticle
    template_name = "cms/news_detail.html"
    context_object_name = "article"
    slug_field = "slug"

    def get_queryset(self):
        return NewsArticle.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "News", "url_name": "cms:news_list"},
            {"label": self.object.title},
        ]
        return context


class FAQListView(ListView):
    template_name = "cms/faq_list.html"
    context_object_name = "faqs"

    def get_queryset(self):
        return get_published_faqs()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "FAQs"},
        ]
        grouped = {}
        for faq in context["faqs"]:
            cat = faq.category.name if faq.category else "General"
            grouped.setdefault(cat, []).append(faq)
        context["faq_groups"] = grouped
        return context


class DownloadsListView(ListView):
    template_name = "cms/downloads_list.html"
    context_object_name = "downloads"

    def get_queryset(self):
        return get_published_downloads()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Downloads"},
        ]
        return context
