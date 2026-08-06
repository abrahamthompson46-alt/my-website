from django.urls import path, re_path

from marketing.views import (
    AuthorDetailView,
    BlogDetailView,
    BlogListView,
    CaseStudyDetailView,
    CaseStudyListView,
    EventDetailView,
    EventListView,
    MarketingHubView,
    NewsletterSubscribeView,
    ResourceListView,
    SuccessStoryDetailView,
    SuccessStoryListView,
    WhitePaperDetailView,
    WhitePaperListView,
)

app_name = "marketing"

urlpatterns = [
    path("", MarketingHubView.as_view(), name="hub"),
    path("blog/", BlogListView.as_view(), name="blog_list"),
    path("blog/category/<slug:category_slug>/", BlogListView.as_view(), name="blog_category"),
    path("blog/tag/<slug:tag_slug>/", BlogListView.as_view(), name="blog_tag"),
    re_path(r"^blog/(?P<slug>[-a-zA-Z0-9_.]+)/$", BlogDetailView.as_view(), name="blog_detail"),
    path("authors/<slug:slug>/", AuthorDetailView.as_view(), name="author_detail"),
    path("events/", EventListView.as_view(), name="events"),
    path("events/<slug:slug>/", EventDetailView.as_view(), name="event_detail"),
    path("success-stories/", SuccessStoryListView.as_view(), name="success_stories"),
    path("success-stories/<slug:slug>/", SuccessStoryDetailView.as_view(), name="success_story_detail"),
    path("case-studies/", CaseStudyListView.as_view(), name="case_studies"),
    path("case-studies/<slug:slug>/", CaseStudyDetailView.as_view(), name="case_study_detail"),
    path("whitepapers/", WhitePaperListView.as_view(), name="whitepapers"),
    path("whitepapers/<slug:slug>/", WhitePaperDetailView.as_view(), name="whitepaper_detail"),
    path("resources/", ResourceListView.as_view(), name="resources"),
    path("newsletter/subscribe/", NewsletterSubscribeView.as_view(), name="newsletter_subscribe"),
]
