from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from accounts.services.email import get_or_create_security_profile
from customer_portal.models import Invoice, Subscription, SupportTicket
from customer_portal.models.invoice import InvoiceStatus
from customer_portal.models.subscription import SubscriptionStatus
from organizations.services import add_member, ensure_default_organization
from organizations.models import MembershipRole
from products.models import Product, ProductCategory, ProductStatus


User = get_user_model()


class APIv1Tests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            username="apia",
            email="apia@example.com",
            password="SecurePass123!",
        )
        self.user_b = User.objects.create_user(
            username="apib",
            email="apib@example.com",
            password="SecurePass123!",
        )
        for user in (self.user_a, self.user_b):
            profile = get_or_create_security_profile(user)
            profile.email_verified = True
            profile.save(update_fields=["email_verified", "updated_at"])

        self.org_a = ensure_default_organization(self.user_a, company="API Alpha")
        self.org_b = ensure_default_organization(self.user_b, company="API Beta")
        category = ProductCategory.objects.create(name="API", slug="api-cat")
        self.product = Product.objects.create(
            name="ChurchHub",
            slug="churchhub-api",
            category=category,
            is_published=True,
            status=ProductStatus.GA,
        )
        self.sub_a = Subscription.objects.create(
            user=self.user_a,
            product=self.product,
            plan_name="Starter",
            status=SubscriptionStatus.TRIAL,
            amount=0,
            currency="GHS",
            started_at="2026-01-01",
            organization=self.org_a,
        )
        self.invoice_a = Invoice.objects.create(
            user=self.user_a,
            invoice_number="INV-API-1",
            amount="10.00",
            currency="GHS",
            status=InvoiceStatus.OPEN,
            issued_at="2026-01-01",
            due_at="2026-01-31",
            organization=self.org_a,
        )
        Invoice.objects.create(
            user=self.user_b,
            invoice_number="INV-API-2",
            amount="20.00",
            currency="GHS",
            status=InvoiceStatus.OPEN,
            issued_at="2026-01-01",
            due_at="2026-01-31",
            organization=self.org_b,
        )
        self.token_a = Token.objects.create(user=self.user_a)
        self.client = APIClient()

    def _auth(self, token=None, org=None):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token or self.token_a.key}")
        headers = {}
        if org is not None:
            headers["HTTP_X_ORGANIZATION_ID"] = str(org.pk)
        return headers

    def test_obtain_token(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {"email": "apia@example.com", "password": "SecurePass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)

    def test_me_lists_memberships(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_a.key}")
        response = self.client.get("/api/v1/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "apia@example.com")
        self.assertEqual(len(response.data["memberships"]), 1)

    def test_subscriptions_require_org_header(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_a.key}")
        response = self.client.get("/api/v1/subscriptions/")
        self.assertEqual(response.status_code, 403)

    def test_subscriptions_are_org_scoped(self):
        headers = self._auth(org=self.org_a)
        response = self.client.get("/api/v1/subscriptions/", **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["plan_name"], "Starter")

    def test_cannot_read_other_org_invoice(self):
        other_invoice = Invoice.objects.get(invoice_number="INV-API-2")
        headers = self._auth(org=self.org_a)
        response = self.client.get(f"/api/v1/invoices/{other_invoice.pk}/", **headers)
        self.assertEqual(response.status_code, 404)

    def test_foreign_org_header_rejected(self):
        headers = self._auth(org=self.org_b)
        response = self.client.get("/api/v1/invoices/", **headers)
        self.assertEqual(response.status_code, 403)

    def test_member_can_create_ticket_in_shared_org(self):
        add_member(organization=self.org_a, user=self.user_b, role=MembershipRole.MEMBER)
        token_b = Token.objects.create(user=self.user_b)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token_b.key}")
        response = self.client.post(
            "/api/v1/tickets/",
            {"subject": "API help", "description": "Need onboarding", "priority": "normal"},
            format="json",
            HTTP_X_ORGANIZATION_ID=str(self.org_a.pk),
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            SupportTicket.objects.filter(
                organization=self.org_a,
                subject="API help",
                user=self.user_b,
            ).exists()
        )
