from django.conf import settings
from django.contrib import messages
from django.db import connection
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView

from cms.services import build_home_context
from core.seo.context import home_seo
from core.seo.mixins import SEOContextMixin
from marketing.forms import NewsletterSubscribeForm
from products.models import Product, ProductDemoRequest
from website.forms import DemoRequestForm
from website.services.homepage import get_homepage_featured_products


class LegalPageMixin(SEOContextMixin, TemplateView):
    """Shared legal/trust page layout."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from control_room.services import get_platform_settings

            context["support_sla_hours"] = get_platform_settings().support_sla_hours
        except Exception:
            context["support_sla_hours"] = 24
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": self.page_title},
        ]
        return context


class PrivacyPolicyView(LegalPageMixin):
    template_name = "website/legal/privacy.html"
    page_title = "Privacy Policy"
    seo_title = "Privacy Policy"
    seo_description = "How we collect, use, and protect your personal information."


class TermsOfServiceView(LegalPageMixin):
    template_name = "website/legal/terms.html"
    page_title = "Terms of Service"
    seo_title = "Terms of Service"
    seo_description = "Terms governing use of our website, products, and customer portal."


class SecurityOverviewView(LegalPageMixin):
    template_name = "website/legal/security.html"
    page_title = "Security"
    seo_title = "Security Overview"
    seo_description = "Security controls, data protection practices, and responsible disclosure."


class RefundPolicyView(LegalPageMixin):
    template_name = "website/legal/refund.html"
    page_title = "Refund Policy"
    seo_title = "Refund & Cancellation Policy"
    seo_description = "Subscription cancellation, refunds, and billing dispute process."


class StatusPageView(TemplateView):
    template_name = "website/status.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        checks = {"database": "unknown", "cache": "unknown"}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks["database"] = "operational"
        except Exception as exc:
            checks["database"] = str(exc)

        try:
            from django.core.cache import cache

            cache.set("status_probe", "ok", 5)
            checks["cache"] = "operational" if cache.get("status_probe") == "ok" else "degraded"
        except Exception as exc:
            checks["cache"] = str(exc)

        try:
            from control_room.services import get_platform_settings

            ps = get_platform_settings()
            sla_hours = ps.support_sla_hours
            support_email = ps.support_email
        except Exception:
            sla_hours = 24
            support_email = getattr(settings, "SUPPORT_EMAIL", "")

        overall = "operational" if checks["database"] == "operational" else "degraded"
        context.update(
            {
                "overall_status": overall,
                "checks": checks,
                "support_sla_hours": sla_hours,
                "support_email": support_email,
                "breadcrumb_items": [
                    {"label": "Home", "url_name": "website:home"},
                    {"label": "System Status"},
                ],
            }
        )
        return context


@method_decorator(cache_page(settings.PUBLIC_PAGE_CACHE_SECONDS), name="dispatch")
class HomeView(TemplateView):
    template_name = "website/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_home_context())
        context["featured_products"] = get_homepage_featured_products()
        context.setdefault("demo_form", DemoRequestForm())
        context.setdefault("newsletter_form", NewsletterSubscribeForm())
        context["seo_meta"] = home_seo(self.request)
        return context

    def post(self, request, *args, **kwargs):
        from common.services.demo_requests import (
            is_demo_rate_limited,
            log_demo_rate_limit,
            log_demo_submission,
        )

        if "demo_submit" in request.POST:
            if is_demo_rate_limited(request):
                log_demo_rate_limit(request)
                messages.error(request, "Too many demo requests. Please try again later.")
                return redirect(reverse("website:home") + "#request-demo")

            form = DemoRequestForm(request.POST)
            if form.is_valid():
                product_interest = form.cleaned_data.get("product_interest")
                product = None
                if product_interest and product_interest not in ("", "multiple"):
                    product = Product.objects.filter(pk=product_interest).first()
                demo = ProductDemoRequest.objects.create(
                    product=product,
                    full_name=form.cleaned_data["full_name"],
                    work_email=form.cleaned_data["work_email"],
                    company=form.cleaned_data["company"],
                    phone=form.cleaned_data.get("phone", ""),
                    message=form.cleaned_data.get("message", ""),
                    source="homepage",
                )
                log_demo_submission(request, demo)
                messages.success(
                    request,
                    "Thank you! Our team will contact you within one business day to schedule your demo.",
                )
                return redirect(reverse("website:home") + "#request-demo")
            context = self.get_context_data(demo_form=form)
            return self.render_to_response(context)

        if "newsletter_submit" in request.POST:
            form = NewsletterSubscribeForm(request.POST)
            if form.is_valid():
                form.save(source="homepage")
                messages.success(request, "You're subscribed! Check your inbox for a confirmation email.")
                return redirect(reverse("website:home") + "#newsletter")
            context = self.get_context_data(newsletter_form=form)
            return self.render_to_response(context)

        return self.get(request, *args, **kwargs)
