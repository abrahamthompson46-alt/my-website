from django.urls import path

from cms.views import DownloadsListView, FAQListView, NewsDetailView, NewsListView

app_name = "cms"

urlpatterns = [
    path("news/", NewsListView.as_view(), name="news_list"),
    path("news/<slug:slug>/", NewsDetailView.as_view(), name="news_detail"),
    path("faqs/", FAQListView.as_view(), name="faq_list"),
    path("downloads/", DownloadsListView.as_view(), name="downloads_list"),
]
