from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from common.services.demo_requests import (
    is_demo_rate_limited,
    log_demo_rate_limit,
    log_demo_submission,
)
from contact.forms import INTENT_CHOICES, ContactLeadForm
from core.seo.mixins import SEOContextMixin
from products.models import Product, ProductDemoRequest


class ContactView(SEOContextMixin, TemplateView):
    template_name = "contact/form.html"
    seo_title = "Contact Sales"
    seo_description = "Request a demo or start your free trial. Our team responds within one business day."

    def _resolve_intent(self):
        url_name = getattr(self.request.resolver_match, "url_name", "")
        if url_name == "trial":
            return "trial"
        if url_name == "demo":
            return "demo"
        intent = self.request.GET.get("intent", "demo")
        return intent if intent in dict(INTENT_CHOICES) else "demo"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        intent = self._resolve_intent()
        context["form"] = kwargs.get("form", ContactLeadForm(initial_intent=intent))
        context["intent"] = intent
        context["intent_labels"] = dict(INTENT_CHOICES)
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Contact"},
        ]
        context["benefits"] = [
            {"icon": "calendar", "title": "Personalized walkthrough", "text": "See the products that fit your organization."},
            {"icon": "zap", "title": "Free trial access", "text": "Full feature access — no credit card required."},
            {"icon": "headphones", "title": "Expert onboarding", "text": "Dedicated support from day one."},
        ]
        return context

    def post(self, request, *args, **kwargs):
        if is_demo_rate_limited(request):
            log_demo_rate_limit(request)
            messages.error(request, "Too many requests. Please try again in an hour.")
            return redirect(request.path)

        form = ContactLeadForm(request.POST, initial_intent=self._resolve_intent())
        if form.is_valid():
            product_interest = form.cleaned_data.get("product_interest")
            product = None
            if product_interest and product_interest not in ("", "multiple"):
                product = Product.objects.filter(pk=product_interest).first()

            intent = form.cleaned_data.get("intent", "demo")
            demo = ProductDemoRequest.objects.create(
                product=product,
                full_name=form.cleaned_data["full_name"],
                work_email=form.cleaned_data["work_email"],
                company=form.cleaned_data["company"],
                phone=form.cleaned_data.get("phone", ""),
                message=form.cleaned_data.get("message", ""),
                source=f"contact-{intent}",
            )
            log_demo_submission(request, demo)

            if intent == "trial":
                messages.success(
                    request,
                    "Thanks! We'll set up your free trial and email you within one business day.",
                )
            else:
                messages.success(
                    request,
                    "Thanks! Our team will contact you within one business day to schedule your demo.",
                )
            return redirect(request.path + "?submitted=1")

        return self.render_to_response(self.get_context_data(form=form))
