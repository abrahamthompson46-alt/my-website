from django.views.generic import TemplateView


class CareersListView(TemplateView):
    template_name = "careers/list.html"
