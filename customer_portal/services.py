"""Customer portal data helpers."""

from django.db.models import Q

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


def get_dashboard_stats(user, organization=None):
    if organization is not None:
        subscriptions = Subscription.objects.filter(organization=organization)
        licenses = License.objects.filter(organization=organization)
        invoices = Invoice.objects.filter(organization=organization)
        tickets = SupportTicket.objects.filter(organization=organization)
        unread_notifications = PortalNotification.objects.filter(user=user).filter(
            Q(organization=organization) | Q(organization__isnull=True),
            is_read=False,
        )
    else:
        subscriptions = Subscription.objects.filter(user=user)
        licenses = License.objects.filter(user=user)
        invoices = Invoice.objects.filter(user=user)
        tickets = SupportTicket.objects.filter(user=user)
        unread_notifications = PortalNotification.objects.filter(user=user, is_read=False)
    return {
        "active_subscriptions": subscriptions.filter(
            status__in=["active", "trial"]
        ).count(),
        "active_licenses": licenses.filter(status="active").count(),
        "open_invoices": invoices.filter(status__in=["open", "overdue"]).count(),
        "open_tickets": tickets.filter(status__in=["open", "in_progress", "waiting"]).count(),
        "unread_notifications": unread_notifications.count(),
    }


def get_recent_notifications(user, organization=None, limit=5):
    qs = PortalNotification.objects.filter(user=user)
    if organization is not None:
        qs = qs.filter(Q(organization=organization) | Q(organization__isnull=True))
    return qs.order_by("-created_at")[:limit]


def get_product_updates_for_user(user, organization=None, limit=5):
    subs = Subscription.objects.filter(status__in=["active", "trial"])
    if organization is not None:
        product_ids = subs.filter(organization=organization).values_list("product_id", flat=True)
    else:
        product_ids = subs.filter(user=user).values_list("product_id", flat=True)
    return ProductUpdate.objects.filter(
        product_id__in=product_ids, is_published=True
    ).select_related("product").order_by("-published_at")[:limit]


def get_subscribed_products(user, organization=None):
    qs = Subscription.objects.filter(status__in=["active", "trial"]).select_related("product")
    if organization is not None:
        return qs.filter(organization=organization)
    return qs.filter(user=user)
