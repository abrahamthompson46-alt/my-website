from django.shortcuts import render


def handler404(request, exception):
    return render(
        request,
        "errors/404.html",
        {"breadcrumb_items": [{"label": "Home", "url_name": "website:home"}, {"label": "404"}]},
        status=404,
    )


def handler500(request):
    return render(request, "errors/500.html", status=500)
