from django.urls import path



from pages.views import AboutView, PageDetailView, PageListView



app_name = "pages"



urlpatterns = [

    path("", PageListView.as_view(), name="list"),

    path("about/", AboutView.as_view(), name="about"),

    path("<slug:slug>/", PageDetailView.as_view(), name="detail"),

]

