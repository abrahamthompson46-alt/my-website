from django.contrib import messages
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, ListView, TemplateView, View

from cms.models import HeroBanner, HeroPlacement
from core.seo.mixins import SEOContextMixin
from marketing.forms import NewsletterSubscribeForm, WhitePaperAccessForm
from marketing.models import (
    Author,
    BlogCategory,
    BlogPost,
    BlogTag,
    CaseStudy,
    MarketingEvent,
    MarketingResource,
    SuccessStory,
    WhitePaper,
)


class MarketingHubView(SEOContextMixin, TemplateView):
    template_name = "marketing/hub.html"
    seo_title = "Resources"
    seo_description = "Blog posts, events, case studies, white papers, and downloadable resources."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_posts"] = BlogPost.objects.filter(is_published=True, is_featured=True)[:3]
        context["upcoming_events"] = MarketingEvent.objects.filter(
            is_published=True, starts_at__gte=timezone.now()
        ).order_by("starts_at")[:3]
        context["success_stories"] = SuccessStory.objects.filter(is_published=True, is_featured=True)[:3]
        context["whitepapers"] = WhitePaper.objects.filter(is_published=True, is_featured=True)[:3]
        context["breadcrumb_items"] = [{"label": "Home", "url_name": "website:home"}, {"label": "Resources"}]
        return context


@method_decorator(cache_page(settings.PUBLIC_PAGE_CACHE_SECONDS), name="dispatch")
class BlogListView(SEOContextMixin, ListView):
    model = BlogPost
    template_name = "marketing/blog_list.html"
    context_object_name = "posts"
    paginate_by = 9
    seo_title = "Blog"
    seo_description = "Insights, product updates, and guides from our team."
    seo_og_image = "/static/images/og/blog.svg"

    def get_queryset(self):
        qs = BlogPost.objects.filter(is_published=True).select_related("category", "author").prefetch_related("tags")
        tag_slug = self.kwargs.get("tag_slug")
        category_slug = self.kwargs.get("category_slug")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)
        return qs.order_by("-published_at", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = BlogCategory.objects.all()
        context["tags"] = BlogTag.objects.all()[:20]
        context["active_category"] = self.kwargs.get("category_slug")
        context["active_tag"] = self.kwargs.get("tag_slug")
        context["hero"] = HeroBanner.objects.filter(is_active=True, placement=HeroPlacement.BLOG).first()
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Resources", "url_name": "marketing:hub"},
            {"label": "Blog"},
        ]
        return context


class BlogDetailView(SEOContextMixin, DetailView):
    model = BlogPost
    template_name = "marketing/blog_detail.html"
    context_object_name = "post"
    slug_field = "slug"

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True).select_related("category", "author").prefetch_related("tags")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        context["related_posts"] = (
            BlogPost.objects.filter(is_published=True, category=post.category)
            .exclude(pk=post.pk)
            .order_by("-published_at")[:3]
        )
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Blog", "url_name": "marketing:blog_list"},
            {"label": post.title},
        ]
        return context


class AuthorDetailView(SEOContextMixin, DetailView):
    model = Author
    template_name = "marketing/author_detail.html"
    context_object_name = "author"
    slug_field = "slug"

    def get_queryset(self):
        return Author.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["posts"] = self.object.posts.filter(is_published=True).order_by("-published_at")
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Blog", "url_name": "marketing:blog_list"},
            {"label": self.object.full_name},
        ]
        return context


class EventListView(SEOContextMixin, ListView):
    model = MarketingEvent
    template_name = "marketing/events.html"
    context_object_name = "events"
    paginate_by = 12
    seo_title = "Events"
    seo_description = "Upcoming webinars, workshops, and conferences."

    def get_queryset(self):
        return MarketingEvent.objects.filter(is_published=True).order_by("starts_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        context["upcoming_events"] = MarketingEvent.objects.filter(is_published=True, starts_at__gte=now).order_by("starts_at")
        context["past_events"] = MarketingEvent.objects.filter(is_published=True, starts_at__lt=now).order_by("-starts_at")[:6]
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Resources", "url_name": "marketing:hub"},
            {"label": "Events"},
        ]
        return context


class EventDetailView(SEOContextMixin, DetailView):
    model = MarketingEvent
    template_name = "marketing/event_detail.html"
    context_object_name = "event"
    slug_field = "slug"

    def get_queryset(self):
        return MarketingEvent.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Events", "url_name": "marketing:events"},
            {"label": self.object.title},
        ]
        return context


class SuccessStoryListView(SEOContextMixin, ListView):
    model = SuccessStory
    template_name = "marketing/success_stories.html"
    context_object_name = "stories"
    seo_title = "Success Stories"
    seo_description = "Customer success stories and outcomes."

    def get_queryset(self):
        return SuccessStory.objects.filter(is_published=True).select_related("product")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Resources", "url_name": "marketing:hub"},
            {"label": "Success Stories"},
        ]
        return context


class SuccessStoryDetailView(SEOContextMixin, DetailView):
    model = SuccessStory
    template_name = "marketing/success_story_detail.html"
    context_object_name = "story"
    slug_field = "slug"

    def get_queryset(self):
        return SuccessStory.objects.filter(is_published=True).select_related("product")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Success Stories", "url_name": "marketing:success_stories"},
            {"label": self.object.title},
        ]
        return context


class CaseStudyListView(SEOContextMixin, ListView):
    model = CaseStudy
    template_name = "marketing/case_studies.html"
    context_object_name = "case_studies"
    seo_title = "Case Studies"
    seo_description = "In-depth case studies from enterprise customers."

    def get_queryset(self):
        return CaseStudy.objects.filter(is_published=True).select_related("product")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Resources", "url_name": "marketing:hub"},
            {"label": "Case Studies"},
        ]
        return context


class CaseStudyDetailView(SEOContextMixin, DetailView):
    model = CaseStudy
    template_name = "marketing/case_study_detail.html"
    context_object_name = "case_study"
    slug_field = "slug"

    def get_queryset(self):
        return CaseStudy.objects.filter(is_published=True).select_related("product")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Case Studies", "url_name": "marketing:case_studies"},
            {"label": self.object.title},
        ]
        return context


class WhitePaperListView(SEOContextMixin, ListView):
    model = WhitePaper
    template_name = "marketing/whitepapers.html"
    context_object_name = "whitepapers"
    seo_title = "White Papers"
    seo_description = "Research and white papers on enterprise software topics."

    def get_queryset(self):
        return WhitePaper.objects.filter(is_published=True).select_related("product")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Resources", "url_name": "marketing:hub"},
            {"label": "White Papers"},
        ]
        return context


class WhitePaperDetailView(SEOContextMixin, DetailView):
    model = WhitePaper
    template_name = "marketing/whitepaper_detail.html"
    context_object_name = "whitepaper"
    slug_field = "slug"

    def get_queryset(self):
        return WhitePaper.objects.filter(is_published=True).select_related("product")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["access_form"] = kwargs.get("access_form", WhitePaperAccessForm())
        context["has_access"] = self.request.session.get(f"whitepaper_access_{self.object.pk}", False)
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "White Papers", "url_name": "marketing:whitepapers"},
            {"label": self.object.title},
        ]
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = WhitePaperAccessForm(request.POST)
        if form.is_valid():
            form.save(source=f"whitepaper:{self.object.slug}")
            request.session[f"whitepaper_access_{self.object.pk}"] = True
            messages.success(request, "Access granted. You can now download the white paper.")
            return redirect(self.object.get_absolute_url())
        return self.render_to_response(self.get_context_data(access_form=form))


class ResourceListView(SEOContextMixin, ListView):
    model = MarketingResource
    template_name = "marketing/resources.html"
    context_object_name = "resources"
    seo_title = "Resources"
    seo_description = "Guides, templates, and tools for your team."

    def get_queryset(self):
        qs = MarketingResource.objects.filter(is_published=True).select_related("product")
        resource_type = self.request.GET.get("type")
        if resource_type:
            qs = qs.filter(resource_type=resource_type)
        return qs

    def get_context_data(self, **kwargs):
        from marketing.models import ResourceType

        context = super().get_context_data(**kwargs)
        context["resource_types"] = ResourceType.choices
        context["active_type"] = self.request.GET.get("type")
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Resources", "url_name": "marketing:hub"},
            {"label": "All Resources"},
        ]
        return context


class NewsletterSubscribeView(View):
    def post(self, request):
        form = NewsletterSubscribeForm(request.POST)
        next_url = request.POST.get("next") or reverse("website:home")
        if form.is_valid():
            form.save(source=request.POST.get("source", "website"))
            messages.success(request, "You're subscribed! Check your inbox for updates.")
        else:
            messages.error(request, "Please enter a valid email address.")
        return redirect(next_url)
