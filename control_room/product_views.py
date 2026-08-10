"""Control room product catalog management."""

from django.contrib import messages
from django.db.models import Count
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.models import AuditEventType
from accounts.services.audit import log_audit_event
from control_room.forms import PlanFeatureForm, PricingPlanForm, PricingTierForm, ProductForm
from control_room.mixins import ControlRoomMixin
from control_room.services import log_control_change
from customer_portal.models import Subscription
from products.models import PlanFeature, PricingPlan, PricingTier, Product, ProductDemoRequest

PricingTierFormSet = inlineformset_factory(
    PricingPlan,
    PricingTier,
    form=PricingTierForm,
    extra=1,
    can_delete=True,
)
PlanFeatureFormSet = inlineformset_factory(
    PricingPlan,
    PlanFeature,
    form=PlanFeatureForm,
    extra=2,
    can_delete=True,
)


class ProductListView(ControlRoomMixin, ListView):
    help_key = "products"
    model = Product
    template_name = "control_room/products.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        return Product.objects.select_related("category").annotate(
            demo_count=Count("demo_requests"),
            subscription_count=Count("subscriptions"),
        ).order_by("-updated_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Products"},
        ]
        context["published_count"] = Product.objects.filter(is_published=True).count()
        context["total_count"] = Product.objects.count()
        return context


class ProductCreateView(ControlRoomMixin, CreateView):
    help_key = "product_form"
    model = Product
    form_class = ProductForm
    template_name = "control_room/product_form.html"

    def get_success_url(self):
        return reverse("control_room:product_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Products", "url_name": "control_room:products"},
            {"label": "New product"},
        ]
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="products",
            action="create",
            summary=f"Created product: {self.object.name}",
            details={"product_id": str(self.object.pk), "slug": self.object.slug},
        )
        log_audit_event(
            AuditEventType.PRODUCT_CREATED,
            request=self.request,
            user=self.request.user,
            message=f"Created product {self.object.name}",
            metadata={"product_id": str(self.object.pk)},
        )
        messages.success(self.request, f"Product “{self.object.name}” created.")
        return response


class ProductUpdateView(ControlRoomMixin, UpdateView):
    help_key = "product_form"
    model = Product
    form_class = ProductForm
    template_name = "control_room/product_form.html"
    context_object_name = "product"

    def get_success_url(self):
        return reverse("control_room:product_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Products", "url_name": "control_room:products"},
            {"label": self.object.name},
        ]
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        log_control_change(
            self.request.user,
            area="products",
            action="update",
            summary=f"Updated product: {self.object.name}",
            details={"product_id": str(self.object.pk), "fields": list(form.changed_data)},
        )
        log_audit_event(
            AuditEventType.PRODUCT_UPDATED,
            request=self.request,
            user=self.request.user,
            message=f"Updated product {self.object.name}",
            metadata={"product_id": str(self.object.pk), "fields": list(form.changed_data)},
        )
        messages.success(self.request, f"Product “{self.object.name}” saved.")
        return response


class ProductDetailView(ControlRoomMixin, DetailView):
    help_key = "product_detail"
    model = Product
    template_name = "control_room/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.select_related("category").annotate(
            demo_count=Count("demo_requests"),
            subscription_count=Count("subscriptions"),
        )

    def get_context_data(self, **kwargs):
        from control_room.models import ControlChangeLog

        context = super().get_context_data(**kwargs)
        product = self.object
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Products", "url_name": "control_room:products"},
            {"label": product.name},
        ]
        context["recent_demos"] = (
            ProductDemoRequest.objects.filter(product=product)
            .order_by("-created_at")[:10]
        )
        context["recent_subscriptions"] = (
            Subscription.objects.filter(product=product)
            .select_related("user")
            .order_by("-created_at")[:10]
        )
        context["product_changes"] = (
            ControlChangeLog.objects.filter(area="products")
            .filter(details__product_id=str(product.pk))
            .select_related("user")
            .order_by("-created_at")[:10]
        )
        context["demo_stats"] = {
            "new": ProductDemoRequest.objects.filter(product=product, status="new").count(),
            "total": product.demo_count,
        }
        context["pricing_plans"] = (
            product.plans.prefetch_related("tiers", "plan_features").order_by("sort_order", "name")
        )
        context["admin_screenshots_url"] = f"/admin/products/productscreenshot/?product__id__exact={product.pk}"
        context["admin_videos_url"] = f"/admin/products/productvideo/?product__id__exact={product.pk}"
        return context


class ProductPricingListView(ControlRoomMixin, DetailView):
    help_key = "product_pricing"
    model = Product
    template_name = "control_room/product_pricing.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Products", "url_name": "control_room:products"},
            {"label": product.name, "url_name": "control_room:product_detail", "url_kwargs": {"pk": product.pk}},
            {"label": "Pricing"},
        ]
        context["plans"] = product.plans.prefetch_related("tiers", "plan_features").order_by("sort_order", "name")
        return context


class ProductPricingPlanCreateView(ControlRoomMixin, CreateView):
    help_key = "product_pricing_form"
    model = PricingPlan
    form_class = PricingPlanForm
    template_name = "control_room/product_pricing_plan_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs["product_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.product
        if self.request.POST:
            context["tier_formset"] = PricingTierFormSet(self.request.POST)
            context["feature_formset"] = PlanFeatureFormSet(self.request.POST)
        else:
            context["tier_formset"] = PricingTierFormSet()
            context["feature_formset"] = PlanFeatureFormSet()
        context["product"] = product
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Products", "url_name": "control_room:products"},
            {"label": product.name, "url_name": "control_room:product_detail", "url_kwargs": {"pk": product.pk}},
            {"label": "Pricing", "url_name": "control_room:product_pricing", "url_kwargs": {"pk": product.pk}},
            {"label": "New plan"},
        ]
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        tier_formset = context["tier_formset"]
        feature_formset = context["feature_formset"]
        if not (tier_formset.is_valid() and feature_formset.is_valid()):
            return self.render_to_response(self.get_context_data(form=form))
        self.object = form.save(commit=False)
        self.object.product = self.product
        self.object.save()
        tier_formset.instance = self.object
        feature_formset.instance = self.object
        tier_formset.save()
        feature_formset.save()
        log_control_change(
            self.request.user,
            area="products",
            action="create",
            summary=f"Created pricing plan {self.object.name} for {self.product.name}",
            details={"product_id": str(self.product.pk), "plan_id": str(self.object.pk)},
        )
        messages.success(self.request, f"Pricing plan “{self.object.name}” created.")
        return redirect("control_room:product_pricing", pk=self.product.pk)

    def get_success_url(self):
        return reverse("control_room:product_pricing", kwargs={"pk": self.product.pk})


class ProductPricingPlanUpdateView(ControlRoomMixin, UpdateView):
    help_key = "product_pricing_form"
    model = PricingPlan
    form_class = PricingPlanForm
    template_name = "control_room/product_pricing_plan_form.html"
    context_object_name = "plan"

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs["product_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return PricingPlan.objects.filter(product=self.product)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.product
        plan = self.object
        if self.request.POST:
            context["tier_formset"] = PricingTierFormSet(self.request.POST, instance=plan)
            context["feature_formset"] = PlanFeatureFormSet(self.request.POST, instance=plan)
        else:
            context["tier_formset"] = PricingTierFormSet(instance=plan)
            context["feature_formset"] = PlanFeatureFormSet(instance=plan)
        context["product"] = product
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Products", "url_name": "control_room:products"},
            {"label": product.name, "url_name": "control_room:product_detail", "url_kwargs": {"pk": product.pk}},
            {"label": "Pricing", "url_name": "control_room:product_pricing", "url_kwargs": {"pk": product.pk}},
            {"label": plan.name},
        ]
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        tier_formset = context["tier_formset"]
        feature_formset = context["feature_formset"]
        if not (tier_formset.is_valid() and feature_formset.is_valid()):
            return self.render_to_response(self.get_context_data(form=form))
        self.object = form.save()
        tier_formset.save()
        feature_formset.save()
        log_control_change(
            self.request.user,
            area="products",
            action="update",
            summary=f"Updated pricing plan {self.object.name}",
            details={"product_id": str(self.product.pk), "plan_id": str(self.object.pk)},
        )
        messages.success(self.request, f"Pricing plan “{self.object.name}” saved.")
        return redirect("control_room:product_pricing", pk=self.product.pk)

    def get_success_url(self):
        return reverse("control_room:product_pricing", kwargs={"pk": self.product.pk})


class ProductPricingPlanDeleteView(ControlRoomMixin, DeleteView):
    model = PricingPlan

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs["product_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return PricingPlan.objects.filter(product=self.product)

    def delete(self, request, *args, **kwargs):
        plan = self.get_object()
        name = plan.name
        product_pk = self.product.pk
        log_control_change(
            request.user,
            area="products",
            action="delete",
            summary=f"Deleted pricing plan {name}",
            details={"product_id": str(product_pk), "plan_id": str(plan.pk)},
        )
        plan.delete()
        messages.success(request, f"Pricing plan “{name}” deleted.")
        return redirect("control_room:product_pricing", pk=product_pk)
