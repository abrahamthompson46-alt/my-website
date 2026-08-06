"""
Seed customer portal demo data for a demo user.
Usage: python manage.py seed_portal
"""
import random
import string
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Role
from accounts.services.email import get_or_create_security_profile
from accounts.services.rbac import assign_role
from customer_portal.models import (
    CustomerDownload,
    CustomerProfile,
    Invoice,
    License,
    PortalNotification,
    ProductUpdate,
    Subscription,
    SupportTicket,
    TicketMessage,
)
from products.models import Product

User = get_user_model()


class Command(BaseCommand):
    help = "Seed customer portal demo data for demo@example.com / demo1234"

    @transaction.atomic
    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            email="demo@example.com",
            defaults={
                "username": "demo",
                "first_name": "Demo",
                "last_name": "Customer",
                "is_staff": False,
            },
        )
        if created:
            user.set_password("demo1234")
            user.save()
            self.stdout.write("Created demo user: demo@example.com / demo1234")
        elif not user.check_password("demo1234"):
            user.set_password("demo1234")
            user.save()

        profile = get_or_create_security_profile(user)
        if not profile.email_verified:
            profile.mark_email_verified()

        customer_role = Role.objects.filter(slug="customer").first()
        if customer_role:
            assign_role(user, customer_role)

        if Subscription.objects.filter(user=user).exists():
            self.stdout.write(self.style.WARNING("Portal data already exists for demo user."))
            return

        CustomerProfile.objects.get_or_create(
            user=user,
            defaults={
                "company": "Acme Industries",
                "job_title": "IT Director",
                "phone": "+1 555 0100",
                "country": "United States",
                "timezone": "America/New_York",
            },
        )

        products = list(Product.objects.filter(is_published=True).order_by("sort_order")[:4])
        if not products:
            self.stdout.write(self.style.ERROR("No products found. Run seed_products first."))
            return

        today = date.today()
        subscriptions = []
        for i, product in enumerate(products):
            sub = Subscription.objects.create(
                user=user,
                product=product,
                plan_name=["Starter", "Professional", "Enterprise", "Professional"][i % 4],
                status="active",
                billing_interval="annual" if i % 2 else "monthly",
                seats=10 + i * 5,
                amount=Decimal("499.00") + i * 200,
                started_at=today - timedelta(days=90 + i * 10),
                renews_at=today + timedelta(days=275 - i * 10),
            )
            subscriptions.append(sub)

            License.objects.create(
                user=user,
                product=product,
                subscription=sub,
                license_key=str(uuid.uuid4()).replace("-", "").upper()[:24],
                status="active",
                seats=sub.seats,
                activated_at=today - timedelta(days=90),
                expires_at=sub.renews_at,
            )

            Invoice.objects.create(
                user=user,
                subscription=sub,
                invoice_number=f"INV-{today.year}-{1000 + i}",
                description=f"{product.name} — annual subscription",
                amount=sub.amount,
                status="paid" if i < 2 else "open",
                issued_at=today - timedelta(days=30),
                due_at=today + timedelta(days=15),
                paid_at=today - timedelta(days=25) if i < 2 else None,
            )

            ProductUpdate.objects.create(
                product=product,
                title=f"{product.name} — Q3 feature release",
                version=f"2.{i + 1}.0",
                update_type="release",
                summary="Performance improvements, new dashboard widgets, and API enhancements.",
                published_at=timezone.now() - timedelta(days=7 + i),
            )

            CustomerDownload.objects.create(
                user=user,
                product=product,
                title=f"{product.name} Desktop Client",
                description="Latest installer for Windows and macOS.",
                category="installer",
                version=f"2.{i + 1}.0",
                file=ContentFile(b"Demo installer placeholder", name=f"{product.slug}-installer.txt"),
            )

        ticket = SupportTicket.objects.create(
            user=user,
            product=products[0],
            subject="Need help configuring SSO integration",
            description="We are setting up SAML SSO for our organization and need guidance on attribute mapping.",
            status="in_progress",
            priority="high",
            reference="TKT-" + "".join(random.choices(string.digits, k=6)),
        )
        TicketMessage.objects.create(
            ticket=ticket,
            author=user,
            body=ticket.description,
            is_staff=False,
        )
        TicketMessage.objects.create(
            ticket=ticket,
            author=user,
            body="Our IdP is Azure AD. Which attributes should we map to user roles?",
            is_staff=False,
        )

        notifications = [
            ("Invoice ready", "Your latest invoice INV-2026-1002 is ready for review.", "billing", "/app/invoices/"),
            ("Ticket updated", "Support ticket TKT-482910 is in progress.", "support", f"/app/tickets/{ticket.pk}/"),
            ("Product update", f"{products[0].name} v2.1.0 is now available.", "update", "/app/updates/"),
        ]
        for title, message, ntype, link in notifications:
            PortalNotification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=ntype,
                link_url=link,
            )

        self.stdout.write(self.style.SUCCESS("Customer portal demo data seeded."))
        self.stdout.write("Login: demo@example.com / demo1234")
