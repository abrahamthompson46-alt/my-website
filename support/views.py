from django.views.generic import TemplateView


class SupportIndexView(TemplateView):
    template_name = "support/index.html"
