from django.views.generic import TemplateView

from core.seo.mixins import SEOContextMixin


class ContactView(SEOContextMixin, TemplateView):
    template_name = "contact/form.html"
    seo_title = "Contact"
    seo_description = "Get in touch with our sales and support teams."
