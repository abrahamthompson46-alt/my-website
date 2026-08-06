from django.urls import path

from documentation.views import (
    APIListView,
    ArticleDetailView,
    CategoryDetailView,
    CategoryListView,
    DocumentationIndexView,
    DocumentationSearchView,
    DownloadListView,
    SectionArticleListView,
    VideoListView,
)

app_name = "documentation"

urlpatterns = [
    path("", DocumentationIndexView.as_view(), name="index"),
    path("search/", DocumentationSearchView.as_view(), name="search"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("categories/<slug:slug>/", CategoryDetailView.as_view(), name="category"),
    path("getting-started/", SectionArticleListView.as_view(), {"section_slug": "getting-started"}, name="getting_started"),
    path("installation/", SectionArticleListView.as_view(), {"section_slug": "installation"}, name="installation"),
    path("videos/", VideoListView.as_view(), name="videos"),
    path("faqs/", SectionArticleListView.as_view(), {"section_slug": "faqs"}, name="faqs"),
    path("api/", APIListView.as_view(), name="api"),
    path("downloads/", DownloadListView.as_view(), name="downloads"),
    path("release-notes/", SectionArticleListView.as_view(), {"section_slug": "release-notes"}, name="release_notes"),
    path("articles/<slug:slug>/", ArticleDetailView.as_view(), name="article"),
]
