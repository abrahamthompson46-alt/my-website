# Generated manually for tenant backfill

from django.db import migrations
from django.utils import timezone
from django.utils.text import slugify


def backfill_personal_organizations(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Organization = apps.get_model("organizations", "Organization")
    OrganizationMembership = apps.get_model("organizations", "OrganizationMembership")
    Subscription = apps.get_model("customer_portal", "Subscription")
    License = apps.get_model("customer_portal", "License")
    Invoice = apps.get_model("customer_portal", "Invoice")
    Payment = apps.get_model("payments", "Payment")

    for user in User.objects.all().iterator():
        membership = (
            OrganizationMembership.objects.filter(user=user, status="active")
            .select_related("organization")
            .first()
        )
        if membership:
            org = membership.organization
        else:
            name = f"{user.email}'s workspace"
            base = slugify(user.email.split("@")[0] or "org")[:180] or "org"
            slug = base
            n = 1
            while Organization.objects.filter(slug=slug).exists():
                n += 1
                slug = f"{base}-{n}"
            org = Organization.objects.create(
                name=name,
                slug=slug,
                status="active",
                created_by=user,
            )
            OrganizationMembership.objects.create(
                organization=org,
                user=user,
                role="owner",
                status="active",
                invited_by=user,
                joined_at=timezone.now(),
            )

        Subscription.objects.filter(user=user, organization__isnull=True).update(organization=org)
        License.objects.filter(user=user, organization__isnull=True).update(organization=org)
        Invoice.objects.filter(user=user, organization__isnull=True).update(organization=org)
        Payment.objects.filter(user=user, organization__isnull=True).update(organization=org)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0001_tenant_foundation"),
        ("customer_portal", "0003_tenant_foundation"),
        ("payments", "0003_tenant_foundation"),
        ("accounts", "0003_team_and_branding"),
    ]

    operations = [
        migrations.RunPython(backfill_personal_organizations, noop_reverse),
    ]
