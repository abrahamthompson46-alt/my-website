from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from accounts.models import AuditLog, User
from customer_portal.models import Invoice, Subscription, SupportTicket
from customer_portal.models.invoice import InvoiceStatus
from customer_portal.models.subscription import SubscriptionStatus
from customer_portal.models.ticket import TicketStatus
from documentation.models import DocArticle, DocCategory, DocVideo
from marketing.models import BlogPost, MarketingEvent, NewsletterSubscriber
from payments.models import Payment, PaymentStatus, WebhookEvent
from products.models import Product, ProductDemoRequest


def _days_ago(days):
    return timezone.now() - timedelta(days=days)


def get_overview_stats():
    now = timezone.now()
    thirty_days_ago = _days_ago(30)
    seven_days_ago = _days_ago(7)

    payments_qs = Payment.objects.filter(status=PaymentStatus.SUCCEEDED)
    revenue_30d = payments_qs.filter(paid_at__gte=thirty_days_ago).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")
    revenue_7d = payments_qs.filter(paid_at__gte=seven_days_ago).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")

    return {
        "customers": User.objects.filter(is_active=True).count(),
        "new_customers_30d": User.objects.filter(date_joined__gte=thirty_days_ago).count(),
        "products": Product.objects.filter(is_published=True).count(),
        "active_subscriptions": Subscription.objects.filter(
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
        ).count(),
        "open_invoices": Invoice.objects.filter(
            status__in=[InvoiceStatus.OPEN, InvoiceStatus.OVERDUE]
        ).count(),
        "revenue_30d": revenue_30d,
        "revenue_7d": revenue_7d,
        "payments_pending": Payment.objects.filter(
            status__in=[PaymentStatus.PENDING, PaymentStatus.PROCESSING, PaymentStatus.PENDING_CONFIRMATION]
        ).count(),
        "demo_requests_new": ProductDemoRequest.objects.filter(status="new").count(),
        "leads_total": NewsletterSubscriber.objects.filter(is_active=True).count(),
        "open_tickets": SupportTicket.objects.filter(
            status__in=[TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.WAITING]
        ).count(),
        "blog_posts": BlogPost.objects.filter(is_published=True).count(),
        "doc_articles": DocArticle.objects.filter(is_published=True).count(),
        "webhooks_unprocessed": WebhookEvent.objects.filter(processed=False).count(),
    }


def get_revenue_chart(days=14):
    start = _days_ago(days)
    rows = (
        Payment.objects.filter(status=PaymentStatus.SUCCEEDED, paid_at__gte=start)
        .annotate(day=TruncDate("paid_at"))
        .values("day")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("day")
    )
    return list(rows)


def get_signups_chart(days=14):
    start = _days_ago(days)
    return list(
        User.objects.filter(date_joined__gte=start)
        .annotate(day=TruncDate("date_joined"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )


def get_recent_activity(limit=15):
    activities = []

    for log in AuditLog.objects.select_related("user").order_by("-created_at")[:limit]:
        activities.append(
            {
                "type": "audit",
                "title": log.get_event_type_display(),
                "meta": log.message or log.user.email if log.user else "System",
                "timestamp": log.created_at,
                "icon": "shield",
            }
        )

    for payment in Payment.objects.select_related("user").order_by("-created_at")[:8]:
        activities.append(
            {
                "type": "payment",
                "title": f"Payment {payment.reference}",
                "meta": f"{payment.user.email} · {payment.currency} {payment.amount}",
                "timestamp": payment.created_at,
                "icon": "credit-card",
            }
        )

    for demo in ProductDemoRequest.objects.select_related("product").order_by("-created_at")[:8]:
        activities.append(
            {
                "type": "lead",
                "title": f"Demo request from {demo.full_name}",
                "meta": demo.company,
                "timestamp": demo.created_at,
                "icon": "calendar",
            }
        )

    for ticket in SupportTicket.objects.select_related("user").order_by("-created_at")[:8]:
        activities.append(
            {
                "type": "support",
                "title": ticket.subject,
                "meta": f"{ticket.reference} · {ticket.user.email}",
                "timestamp": ticket.created_at,
                "icon": "life-buoy",
            }
        )

    activities.sort(key=lambda item: item["timestamp"], reverse=True)
    return activities[:limit]


def get_product_breakdown():
    return (
        Subscription.objects.filter(status=SubscriptionStatus.ACTIVE)
        .values("product__name")
        .annotate(count=Count("id"))
        .order_by("-count")[:8]
    )


def get_ticket_priority_breakdown():
    return (
        SupportTicket.objects.filter(
            status__in=[TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.WAITING]
        )
        .values("priority")
        .annotate(count=Count("id"))
    )
