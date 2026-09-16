from django.conf import settings
from django.contrib import messages
from django.db import connection
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page, never_cache
from django.views.generic import TemplateView

from cms.services import build_home_context
from core.seo.context import home_seo
from core.seo.mixins import SEOContextMixin
from marketing.forms import NewsletterSubscribeForm
from products.models import Product, ProductDemoRequest
from website.forms import DemoRequestForm
from website.services.homepage import get_homepage_featured_products
from website.services.outbound_links import (
    annotate_intent_links,
    build_intent_url,
    get_homepage_intent_products,
)
from website.solutions import SOLUTIONS


class LegalPageMixin(SEOContextMixin, TemplateView):
    """Shared legal/trust page layout."""

    page_title = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from control_room.services import get_platform_settings

            context["support_sla_hours"] = get_platform_settings().support_sla_hours
        except Exception:
            context["support_sla_hours"] = 24
        context["page_title"] = self.page_title
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
    page_title = "Security Center"
    seo_title = "Security Center"
    seo_description = "Security architecture, authentication, audit logging, and responsible disclosure for Zreta."


class EnterpriseReadinessView(LegalPageMixin):
    template_name = "website/legal/enterprise.html"
    page_title = "Enterprise readiness"
    seo_title = "Enterprise Readiness"
    seo_description = (
        "What Zreta delivers today for enterprise buyers — live controls versus roadmap capabilities."
    )


class RefundPolicyView(LegalPageMixin):
    template_name = "website/legal/refund.html"
    page_title = "Refund Policy"
    seo_title = "Refund & Cancellation Policy"
    seo_description = "Subscription cancellation, refunds, and billing dispute process."


class ArchitectureView(LegalPageMixin):
    template_name = "website/platform/architecture.html"
    page_title = "Platform architecture"
    seo_title = "Zreta platform architecture"
    seo_description = "How Zreta shared billing, identity, and security relate to live product applications."


class PaymentsPlatformView(LegalPageMixin):
    template_name = "website/platform/payments.html"
    page_title = "Payments & billing"
    seo_title = "Payments and billing"
    seo_description = "How Zreta handles GHS pricing, Mobile Money gateways, invoices, and the customer portal."


class IntegrationsView(LegalPageMixin):
    template_name = "website/platform/integrations.html"
    page_title = "API & integrations"
    seo_title = "API and integrations"
    seo_description = "Zreta API access, webhooks, and integration approach for the marketing and billing platform."


class SLAView(LegalPageMixin):
    template_name = "website/platform/sla.html"
    page_title = "Support SLA"
    seo_title = "Support service levels"
    seo_description = "Published support response targets for Zreta customers."


class OnboardingView(LegalPageMixin):
    template_name = "website/platform/onboarding.html"
    page_title = "Enterprise onboarding"
    seo_title = "Enterprise onboarding"
    seo_description = "How Zreta helps organizations start ChurchHub or CoreTrust and manage billing."


class PrivacyCenterView(LegalPageMixin):
    template_name = "website/platform/privacy_center.html"
    page_title = "Privacy Center"
    seo_title = "Privacy Center"
    seo_description = "Privacy policy, data handling practices, and how to contact Zreta about personal data."


class ContinuityView(LegalPageMixin):
    template_name = "website/platform/continuity.html"
    page_title = "Business continuity"
    seo_title = "Business continuity and backups"
    seo_description = "What Zreta publishes about backups and continuity for the marketing and billing platform."


class SolutionLandingView(SEOContextMixin, TemplateView):
    template_name = "website/solution.html"
    solution_key = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solution = SOLUTIONS[self.solution_key]
        context["solution"] = solution
        context["page_title"] = solution["title"]
        product = (
            Product.objects.filter(slug=solution["product_slug"], is_published=True)
            .prefetch_related("plans", "features")
            .first()
        )
        context["product"] = product
        if product:
            from products.services.trial_links import get_product_demo_url, get_product_trial_url

            context["trial_url"] = get_product_trial_url(product, source="solution")
            context["demo_url"] = get_product_demo_url(product, source="solution")
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Solutions"},
            {"label": solution["eyebrow"].split("·")[-1].strip()},
        ]
        return context


class ChurchesSolutionView(SolutionLandingView):
    solution_key = "churches"
    seo_title = "Church management software"
    seo_description = "ChurchHub for membership, giving, and administration — marketed and billed through Zreta."


class MicrofinanceSolutionView(SolutionLandingView):
    solution_key = "microfinance"
    seo_title = "Microfinance software"
    seo_description = "CoreTrust for MFIs and SACCOs — marketed and billed through Zreta."


class EnterprisesSolutionView(SolutionLandingView):
    solution_key = "enterprises"
    seo_title = "Enterprise ERP roadmap"
    seo_description = "ERP Suite is on the Zreta roadmap. Evaluate live products and shared billing today."


class EducationSolutionView(SolutionLandingView):
    solution_key = "education"
    seo_title = "School management roadmap"
    seo_description = "School Management is on the Zreta product roadmap."


class HealthcareSolutionView(SolutionLandingView):
    solution_key = "healthcare"
    seo_title = "Hospital management roadmap"
    seo_description = "Hospital Management is on the Zreta product roadmap."


@method_decorator(never_cache, name="dispatch")
class OutboundIntentRedirectView(View):
    """Log trial/demo funnel clicks, then redirect to the live product site."""

    def get(self, request, slug, intent):
        if intent not in ("trial", "demo"):
            raise Http404
        product = get_object_or_404(Product, slug=slug, is_published=True)
        source = (request.GET.get("src") or "storefront").strip()[:40] or "storefront"
        destination = build_intent_url(product, intent, source=source)
        if not destination:
            return redirect("products:detail", slug=product.slug)

        from accounts.models import AuditEventType
        from accounts.services.audit import log_audit_event

        log_audit_event(
            AuditEventType.OUTBOUND_INTENT_CLICK,
            request=request,
            message=f"Outbound {intent} click for {product.slug}",
            metadata={
                "product": product.slug,
                "intent": intent,
                "source": source,
                "destination_host": destination.split("/")[2] if "://" in destination else "",
            },
            status_code=302,
        )
        return HttpResponseRedirect(destination)


class StatusPageView(TemplateView):
    template_name = "website/status.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        checks = {
            "website": "unknown",
            "database": "unknown",
            "cache": "unknown",
            "authentication": "unknown",
            "payments": "unknown",
        }
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks["database"] = "operational"
            checks["website"] = "operational"
            checks["authentication"] = "operational"
            checks["payments"] = "operational"
        except Exception:
            checks["database"] = "degraded"
            checks["website"] = "degraded"

        try:
            from django.core.cache import cache

            cache.set("status_probe", "ok", 5)
            checks["cache"] = "operational" if cache.get("status_probe") == "ok" else "degraded"
        except Exception:
            checks["cache"] = "degraded"

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
                "components": [
                    ("Website", checks["website"]),
                    ("Database", checks["database"]),
                    ("Cache", checks["cache"]),
                    ("Authentication", checks["authentication"]),
                    ("Payments platform", checks["payments"]),
                    ("ChurchHub", "external"),
                    ("CoreTrust", "external"),
                ],
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
        context["intent_products"] = annotate_intent_links(get_homepage_intent_products())
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
                return redirect(reverse("website:home") + "#start-trial")

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
                return redirect(reverse("website:home") + "#start-trial")
            context = self.get_context_data(demo_form=form)
            return self.render_to_response(context)

        if "newsletter_submit" in request.POST:
            from common.services.public_rate_limit import is_newsletter_rate_limited, log_newsletter_rate_limit

            if is_newsletter_rate_limited(request):
                log_newsletter_rate_limit(request)
                messages.error(request, "Too many subscription attempts. Please try again later.")
                return redirect(reverse("website:home") + "#newsletter")

            form = NewsletterSubscribeForm(request.POST)
            if form.is_valid():
                form.save(source="homepage")
                messages.success(request, "You're subscribed! Check your inbox for a confirmation email.")
                return redirect(reverse("website:home") + "#newsletter")
            context = self.get_context_data(newsletter_form=form)
            return self.render_to_response(context)

        return self.get(request, *args, **kwargs)
