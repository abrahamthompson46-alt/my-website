"""In-app notifications for platform owners on demo requests and payments."""

from django.db.models import Q
from django.urls import reverse

from accounts.models import Role, User
from customer_portal.models.notification import NotificationType, PortalNotification


def get_platform_owner_users():
    """Return active users who can manage operations workflows."""
    role_ids = Role.objects.filter(
        slug__in=("platform-owner", "platform-admin"),
        is_active=True,
    ).values_list("pk", flat=True)
    return (
        User.objects.filter(is_active=True)
        .filter(Q(is_superuser=True) | Q(user_roles__role_id__in=role_ids))
        .distinct()
    )


def _notify_owners(*, title, message, notification_type, link_url):
    owners = list(get_platform_owner_users())
    if not owners:
        return
    PortalNotification.objects.bulk_create(
        [
            PortalNotification(
                user=owner,
                title=title,
                message=message,
                notification_type=notification_type,
                link_url=link_url,
            )
            for owner in owners
        ]
    )


def notify_owners_demo_request(demo):
    product_name = demo.product.name if demo.product_id else "General inquiry"
    customer = demo.full_name or demo.work_email
    _notify_owners(
        title=f"New demo request — {product_name}",
        message=f"{customer} ({demo.work_email}) from {demo.company} submitted a request.",
        notification_type=NotificationType.SUPPORT,
        link_url=reverse("operations:demo_requests"),
    )


def notify_owners_payment(payment):
    customer = payment.user.display_name or payment.user.email
    amount = f"{payment.currency} {payment.amount}"
    if payment.manual_method:
        title = f"Manual payment awaiting confirmation — {payment.reference}"
        message = (
            f"{customer} submitted {amount} via {payment.get_manual_method_display()}. "
            "Review and confirm in Operations."
        )
    else:
        title = f"New payment — {payment.reference}"
        message = f"{customer} initiated {amount} ({payment.get_status_display()})."
    _notify_owners(
        title=title,
        message=message,
        notification_type=NotificationType.BILLING,
        link_url=reverse("operations:payments"),
    )
