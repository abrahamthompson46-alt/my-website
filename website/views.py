from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView

from cms.services import build_home_context
from core.seo.context import home_seo
from marketing.forms import NewsletterSubscribeForm
from products.models import Product, ProductDemoRequest
from website.forms import DemoRequestForm


@method_decorator(cache_page(settings.PUBLIC_PAGE_CACHE_SECONDS), name="dispatch")
class HomeView(TemplateView):
    template_name = "website/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_home_context())
        context["featured_products"] = (
            Product.objects.filter(is_featured=True, is_published=True)
            .prefetch_related("features")
            .order_by("sort_order")
        )
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
