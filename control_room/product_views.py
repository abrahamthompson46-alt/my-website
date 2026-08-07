"""Control room product catalog management."""

from django.contrib import messages
from django.db.models import Count
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.models import AuditEventType
from accounts.services.audit import log_audit_event
from control_room.forms import ProductForm
from control_room.mixins import ControlRoomMixin
from control_room.services import log_control_change
from customer_portal.models import Subscription
from products.models import Product, ProductDemoRequest


class ProductListView(ControlRoomMixin, ListView):
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
        return context
