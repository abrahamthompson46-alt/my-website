from django.db.models import Count
from django.views.generic import DetailView, ListView, TemplateView

from accounts.models import AuditLog, User
from customer_portal.models import Invoice, Subscription, SupportTicket
from documentation.models import DocArticle, DocCategory, DocVideo
from marketing.models import (
    BlogPost,
    CaseStudy,
    MarketingEvent,
    MarketingResource,
    NewsletterSubscriber,
    SuccessStory,
    WhitePaper,
)
from operations.mixins import StaffRequiredMixin
from operations.services.dashboard import (
    get_overview_stats,
    get_product_breakdown,
    get_recent_activity,
    get_revenue_chart,
    get_signups_chart,
    get_ticket_priority_breakdown,
)
from operations.services.health import get_system_health
from payments.models import Payment, ReconciliationRun, Refund, WebhookEvent
from products.models import Product, ProductDemoRequest


class OpsBaseMixin(StaffRequiredMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("breadcrumb_items", [{"label": "Dashboard", "url_name": "operations:dashboard"}])
        return context


class DashboardView(OpsBaseMixin, TemplateView):
    template_name = "operations/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = get_overview_stats()
        context["revenue_chart"] = get_revenue_chart()
        context["signups_chart"] = get_signups_chart()
        context["recent_activity"] = get_recent_activity()
        context["product_breakdown"] = get_product_breakdown()
        context["health"] = get_system_health()
        context["breadcrumb_items"] = [{"label": "Dashboard"}]
        return context


class AnalyticsView(OpsBaseMixin, TemplateView):
    template_name = "operations/analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = get_overview_stats()
        context["revenue_chart"] = get_revenue_chart(30)
        context["signups_chart"] = get_signups_chart(30)
        context["product_breakdown"] = get_product_breakdown()
        context["ticket_breakdown"] = get_ticket_priority_breakdown()
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "operations:dashboard"},
            {"label": "Analytics"},
        ]
        return context


class ProductsView(OpsBaseMixin, ListView):
    model = Product
    template_name = "operations/products.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        return Product.objects.select_related("category").annotate(
            subscription_count=Count("subscriptions"),
            demo_count=Count("demo_requests"),
        ).order_by("-is_featured", "sort_order")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total"] = Product.objects.count()
        context["published"] = Product.objects.filter(is_published=True).count()
        context["breadcrumb_items"].append({"label": "Products"})
        return context


class CustomersView(OpsBaseMixin, ListView):
    model = User
    template_name = "operations/customers.html"
    context_object_name = "customers"
    paginate_by = 25

    def get_queryset(self):
        return (
            User.objects.filter(is_active=True)
            .annotate(
                subscription_count=Count("subscriptions"),
                payment_count=Count("payments"),
            )
            .order_by("-date_joined")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total"] = User.objects.count()
        context["breadcrumb_items"].append({"label": "Customers"})
        return context


class LeadsView(OpsBaseMixin, ListView):
    model = NewsletterSubscriber
    template_name = "operations/leads.html"
    context_object_name = "leads"
    paginate_by = 25

    def get_queryset(self):
        return NewsletterSubscriber.objects.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_count"] = NewsletterSubscriber.objects.filter(is_active=True).count()
        context["breadcrumb_items"].append({"label": "Leads"})
        return context


class DemoRequestsView(OpsBaseMixin, ListView):
    model = ProductDemoRequest
    template_name = "operations/demo_requests.html"
    context_object_name = "demo_requests"
    paginate_by = 25

    def get_queryset(self):
        qs = ProductDemoRequest.objects.select_related("product").order_by("-created_at")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        from products.models.demo import DemoRequestStatus

        context = super().get_context_data(**kwargs)
        context["statuses"] = DemoRequestStatus.choices
        context["active_status"] = self.request.GET.get("status")
        context["new_count"] = ProductDemoRequest.objects.filter(status="new").count()
        context["breadcrumb_items"].append({"label": "Demo Requests"})
        return context


class PaymentsView(OpsBaseMixin, ListView):
    model = Payment
    template_name = "operations/payments.html"
    context_object_name = "payments"
    paginate_by = 25

    def get_queryset(self):
        qs = Payment.objects.select_related("user", "gateway").order_by("-created_at")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        from decimal import Decimal

        from django.db.models import Sum

        from payments.models import PaymentStatus

        context = super().get_context_data(**kwargs)
        context["statuses"] = PaymentStatus.choices
        context["active_status"] = self.request.GET.get("status")
        context["revenue_total"] = Payment.objects.filter(status=PaymentStatus.SUCCEEDED).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")
        context["pending_count"] = Payment.objects.filter(
            status__in=[PaymentStatus.PENDING, PaymentStatus.PENDING_CONFIRMATION, PaymentStatus.PROCESSING]
        ).count()
        context["refund_count"] = Refund.objects.count()
        context["breadcrumb_items"].append({"label": "Payments"})
        return context


class SupportView(OpsBaseMixin, ListView):
    model = SupportTicket
    template_name = "operations/support.html"
    context_object_name = "tickets"
    paginate_by = 25

    def get_queryset(self):
        qs = SupportTicket.objects.select_related("user", "product").order_by("-created_at")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        from customer_portal.models.ticket import TicketStatus

        context = super().get_context_data(**kwargs)
        context["statuses"] = TicketStatus.choices
        context["active_status"] = self.request.GET.get("status")
        context["open_count"] = SupportTicket.objects.filter(
            status__in=["open", "in_progress", "waiting"]
        ).count()
        context["breadcrumb_items"].append({"label": "Support"})
        return context


class DocumentationView(OpsBaseMixin, TemplateView):
    template_name = "operations/documentation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = DocCategory.objects.annotate(article_count=Count("articles")).order_by("sort_order")
        context["articles"] = DocArticle.objects.select_related("category").order_by("-updated_at")[:10]
        context["videos"] = DocVideo.objects.filter(is_published=True).count()
        context["article_count"] = DocArticle.objects.filter(is_published=True).count()
        context["breadcrumb_items"].append({"label": "Documentation"})
        return context


class MarketingView(OpsBaseMixin, TemplateView):
    template_name = "operations/marketing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["counts"] = {
            "blog": BlogPost.objects.filter(is_published=True).count(),
            "events": MarketingEvent.objects.filter(is_published=True).count(),
            "case_studies": CaseStudy.objects.filter(is_published=True).count(),
            "success_stories": SuccessStory.objects.filter(is_published=True).count(),
            "whitepapers": WhitePaper.objects.filter(is_published=True).count(),
            "resources": MarketingResource.objects.filter(is_published=True).count(),
            "subscribers": NewsletterSubscriber.objects.filter(is_active=True).count(),
        }
        context["recent_posts"] = BlogPost.objects.filter(is_published=True).order_by("-published_at")[:5]
        context["upcoming_events"] = MarketingEvent.objects.filter(is_published=True).order_by("starts_at")[:5]
        context["breadcrumb_items"].append({"label": "Marketing"})
        return context


class SystemHealthView(OpsBaseMixin, TemplateView):
    template_name = "operations/system_health.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["health"] = get_system_health()
        context["webhooks"] = WebhookEvent.objects.order_by("-created_at")[:10]
        context["reconciliations"] = ReconciliationRun.objects.order_by("-created_at")[:5]
        context["breadcrumb_items"].append({"label": "System Health"})
        return context


class ActivityLogsView(OpsBaseMixin, ListView):
    model = AuditLog
    template_name = "operations/activity_logs.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user", "actor").order_by("-created_at")
        event_type = self.request.GET.get("event")
        if event_type:
            qs = qs.filter(event_type=event_type)
        return qs

    def get_context_data(self, **kwargs):
        from accounts.models import AuditEventType

        context = super().get_context_data(**kwargs)
        context["event_types"] = AuditEventType.choices
        context["active_event"] = self.request.GET.get("event")
        context["breadcrumb_items"].append({"label": "Activity Logs"})
        return context
