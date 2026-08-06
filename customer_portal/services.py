"""Customer portal data helpers."""

from customer_portal.models import (
    Invoice,
    License,
    PortalNotification,
    ProductUpdate,
    Subscription,
    SupportTicket,
)


def get_or_create_profile(user):
    from customer_portal.models import CustomerProfile

    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    return profile


def get_dashboard_stats(user):
    subscriptions = Subscription.objects.filter(user=user)
    return {
        "active_subscriptions": subscriptions.filter(
            status__in=["active", "trial"]
        ).count(),
        "active_licenses": License.objects.filter(user=user, status="active").count(),
        "open_invoices": Invoice.objects.filter(user=user, status__in=["open", "overdue"]).count(),
        "open_tickets": SupportTicket.objects.filter(
            user=user, status__in=["open", "in_progress", "waiting"]
        ).count(),
        "unread_notifications": PortalNotification.objects.filter(user=user, is_read=False).count(),
    }


def get_recent_notifications(user, limit=5):
    return PortalNotification.objects.filter(user=user).order_by("-created_at")[:limit]


def get_product_updates_for_user(user, limit=5):
    product_ids = Subscription.objects.filter(
        user=user, status__in=["active", "trial"]
    ).values_list("product_id", flat=True)
    return ProductUpdate.objects.filter(
        product_id__in=product_ids, is_published=True
    ).select_related("product").order_by("-published_at")[:limit]


def get_subscribed_products(user):
    return Subscription.objects.filter(
        user=user, status__in=["active", "trial"]
    ).select_related("product")
