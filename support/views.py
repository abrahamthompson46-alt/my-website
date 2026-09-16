from django.views.generic import TemplateView


class SupportIndexView(TemplateView):
    template_name = "support/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from control_room.services import get_platform_settings

            context["support_sla_hours"] = get_platform_settings().support_sla_hours
        except Exception:
            context["support_sla_hours"] = 24
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Support"},
        ]
        return context
