from django.conf import settings
from django.contrib import messages
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, ListView, TemplateView

from cms.models import Testimonial
from cms.services import get_product_hero, get_published_downloads, get_published_faqs
from core.seo.helpers import seo_for_page
from core.seo.mixins import SEOContextMixin
from core.seo.schema import build_faq_schema
from products.forms import ProductCompareSelectForm, ProductDemoRequestForm
from products.models import (
    ComparisonAttribute,
    PricingPlan,
    Product,
    ProductCategory,
    ProductComparisonEntry,
)


class PublishedProductMixin:
    """Restrict views to published catalog entries."""

    def get_queryset(self):
        return (
            Product.objects.filter(is_published=True)
            .select_related("category")
            .prefetch_related(
                "modules",
                "features",
                "screenshots",
                "videos",
                "downloads",
                Prefetch(
                    "plans",
                    queryset=PricingPlan.objects.filter(is_published=True).prefetch_related(
                        "tiers", "plan_features"
                    ),
                ),
            )
        )


@method_decorator(cache_page(settings.PUBLIC_PAGE_CACHE_SECONDS), name="dispatch")
class ProductListView(SEOContextMixin, PublishedProductMixin, ListView):
    template_name = "products/list.html"
    context_object_name = "products"
    paginate_by = 12
    seo_title = "Products"
    seo_description = "Explore our enterprise software products built for modern teams."
    seo_og_image = "/static/images/og/products.svg"

    def get_queryset(self):
        qs = super().get_queryset()
        category_slug = self.kwargs.get("category_slug")
        if category_slug:
            qs = qs.filter(category__slug=category_slug, category__is_active=True)
        return qs.order_by("sort_order", "name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = ProductCategory.objects.filter(is_active=True)
        category_slug = self.kwargs.get("category_slug")
        if category_slug:
            context["active_category"] = get_object_or_404(
                ProductCategory, slug=category_slug, is_active=True
            )
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Products"},
        ]
        return context


class ProductDetailView(SEOContextMixin, PublishedProductMixin, DetailView):
    template_name = "products/detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_template_names(self):
        if getattr(self, "object", None) and self.object.is_future:
            return ["products/coming_soon.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context["demo_form"] = kwargs.get("demo_form", ProductDemoRequestForm(product=product))
        context["related_products"] = (
            Product.objects.filter(is_published=True, category=product.category)
            .exclude(pk=product.pk)
            .order_by("sort_order")[:3]
        )
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Products", "url_name": "products:list"},
            {"label": product.name},
        ]
        context["cms_hero"] = get_product_hero(product)
        context["cms_sections"] = product.cms_sections.filter(is_published=True)
        context["product_faqs"] = get_published_faqs(product)
        context["product_testimonials"] = Testimonial.objects.filter(
            is_published=True, product=product
        ).order_by("sort_order")
        context["cms_downloads"] = get_published_downloads(product)
        return context

    def get_extra_schema(self, context):
        faqs = context.get("product_faqs") or []
        if not faqs:
            return []
        return [
            build_faq_schema([{"question": f.question, "answer": f.answer} for f in faqs])
        ]

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ProductDemoRequestForm(request.POST, product=self.object)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Thank you! We'll contact you shortly about {self.object.name}.",
            )
            return redirect(reverse("products:detail", kwargs={"slug": self.object.slug}) + "#demo")
        context = self.get_context_data(demo_form=form)
        return self.render_to_response(context)


class ProductPricingView(PublishedProductMixin, DetailView):
    template_name = "products/pricing.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context["plans"] = product.plans.filter(is_published=True).prefetch_related("tiers", "plan_features")
        context["demo_form"] = ProductDemoRequestForm(product=product)
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Products", "url_name": "products:list"},
            {"label": product.name, "url": product.get_absolute_url()},
            {"label": "Pricing"},
        ]
        return context


class ProductCompareView(TemplateView):
    template_name = "products/compare.html"

    def get_compare_products(self, slugs):
        if not slugs:
            return Product.objects.none()
        products = list(
            Product.objects.filter(is_published=True, slug__in=slugs)
            .prefetch_related("comparison_entries__attribute")
            .order_by("sort_order")
        )
        slug_order = {slug: i for i, slug in enumerate(slugs)}
        products.sort(key=lambda p: slug_order.get(p.slug, 999))
        return products

    def get_comparison_matrix(self, products):
        attributes = ComparisonAttribute.objects.filter(is_active=True)
        matrix = []
        current_group = None
        for attribute in attributes:
            if attribute.group != current_group:
                current_group = attribute.group
                if current_group:
                    matrix.append({"type": "group", "label": current_group})
            row = {"type": "row", "attribute": attribute, "values": {}}
            for product in products:
                entry = ProductComparisonEntry.objects.filter(
                    product=product, attribute=attribute
                ).first()
                row["values"][product.slug] = entry.display_value if entry else "—"
            matrix.append(row)
        return matrix

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slugs = self.request.GET.getlist("p")
        products = self.get_compare_products(slugs)
        context["selected_products"] = products
        context["compare_form"] = kwargs.get(
            "compare_form",
            ProductCompareSelectForm(
                initial={"products": [p.pk for p in products]} if products else None
            ),
        )
        if len(products) >= 2:
            context["comparison_matrix"] = self.get_comparison_matrix(products)
        context["all_products"] = Product.objects.filter(is_published=True).order_by("sort_order")
        context["breadcrumb_items"] = [
            {"label": "Home", "url_name": "website:home"},
            {"label": "Products", "url_name": "products:list"},
            {"label": "Compare"},
        ]
        return context

    def post(self, request, *args, **kwargs):
        form = ProductCompareSelectForm(request.POST)
        if form.is_valid():
            slugs = list(form.cleaned_data["products"].values_list("slug", flat=True))
            query = "&".join(f"p={slug}" for slug in slugs)
            return redirect(f"{reverse('products:compare')}?{query}")
        return self.render_to_response(self.get_context_data(compare_form=form))
