# Generated manually for tenant support-asset backfill

from django.db import migrations


def backfill_support_assets(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    OrganizationMembership = apps.get_model("organizations", "OrganizationMembership")
    SupportTicket = apps.get_model("customer_portal", "SupportTicket")
    CustomerDownload = apps.get_model("customer_portal", "CustomerDownload")
    PortalNotification = apps.get_model("customer_portal", "PortalNotification")

    for user in User.objects.all().iterator():
        membership = (
            OrganizationMembership.objects.filter(user=user, status="active")
            .order_by("created_at")
            .first()
        )
        if not membership:
            continue
        org = membership.organization
        SupportTicket.objects.filter(user=user, organization__isnull=True).update(organization=org)
        CustomerDownload.objects.filter(user=user, organization__isnull=True).update(organization=org)
        # Keep platform-wide/personal notifications without forcing org when already null
        # and title suggests owner ops — only backfill customer-looking rows with no org.
        PortalNotification.objects.filter(user=user, organization__isnull=True).exclude(
            notification_type__in=("billing", "support")
        ).update(organization=org)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("customer_portal", "0004_tenant_support_assets"),
        ("organizations", "0002_backfill_personal_orgs"),
    ]

    operations = [
        migrations.RunPython(backfill_support_assets, noop_reverse),
    ]
