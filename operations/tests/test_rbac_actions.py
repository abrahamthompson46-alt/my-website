"""RBAC regression tests for operations POST actions."""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User
from accounts.services.email import get_or_create_security_profile
from accounts.services.rbac import assign_role
from customer_portal.models.ticket import SupportTicket, TicketStatus
from payments.constants import MANUAL
from payments.models import GatewayConfiguration, Payment, PaymentStatus
from products.models import Product, ProductCategory
from products.models.demo import DemoRequestStatus, ProductDemoRequest


class OperationsActionsRBACTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="ops-owner",
            email="ops-owner@example.com",
            password="pass",
            is_staff=True,
        )
        self.staff = User.objects.create_user(
            username="ops-staff",
            email="ops-staff@example.com",
            password="pass",
            is_staff=True,
        )
        owner_role = Role.objects.create(name="Platform Owner", slug="platform-owner")
        assign_role(self.owner, owner_role)
        for user in (self.owner, self.staff):
            profile = get_or_create_security_profile(user)
            profile.email_verified = True
            profile.mfa_enabled = True
            profile.save(update_fields=["email_verified", "mfa_enabled"])

        category = ProductCategory.objects.create(name="Platform", slug="platform")
        self.product = Product.objects.create(
            name="ChurchHub",
            slug="churchhub",
            category=category,
            is_published=True,
        )
        self.demo = ProductDemoRequest.objects.create(
            product=self.product,
            full_name="Demo User",
            work_email="demo@example.com",
            company="Acme",
            status=DemoRequestStatus.NEW,
        )
        self.customer = User.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="pass",
        )
        self.ticket = SupportTicket.objects.create(
            user=self.customer,
            product=self.product,
            subject="Help",
            description="Need support",
            status=TicketStatus.OPEN,
            reference="TKT-1001",
        )
        GatewayConfiguration.objects.create(code=MANUAL, name="Manual", is_active=True, is_default=True)
        self.gateway = GatewayConfiguration.objects.get(code=MANUAL)
        self.payment = Payment.objects.create(
            user=self.customer,
            gateway=self.gateway,
            amount=Decimal("49.00"),
            currency="GHS",
            status=PaymentStatus.PENDING_CONFIRMATION,
            reference="PAY-1001",
        )

    def test_staff_cannot_update_demo_request(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("operations:demo_request_update", kwargs={"pk": self.demo.pk}),
            {"status": DemoRequestStatus.CONTACTED},
        )
        self.assertEqual(response.status_code, 403)
        self.demo.refresh_from_db()
        self.assertEqual(self.demo.status, DemoRequestStatus.NEW)

    def test_owner_can_update_demo_request(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("operations:demo_request_update", kwargs={"pk": self.demo.pk}),
            {"status": DemoRequestStatus.CONTACTED},
        )
        self.assertEqual(response.status_code, 302)
        self.demo.refresh_from_db()
        self.assertEqual(self.demo.status, DemoRequestStatus.CONTACTED)

    def test_staff_cannot_update_support_ticket(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("operations:support_ticket_update", kwargs={"pk": self.ticket.pk}),
            {"status": TicketStatus.RESOLVED},
        )
        self.assertEqual(response.status_code, 403)

    def test_staff_cannot_confirm_manual_payment(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("operations:payment_confirm", kwargs={"pk": self.payment.pk}),
            {"notes": "confirmed"},
        )
        self.assertEqual(response.status_code, 403)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, PaymentStatus.PENDING_CONFIRMATION)

    def test_staff_can_view_ops_dashboard(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("operations:dashboard"))
        self.assertEqual(response.status_code, 200)
