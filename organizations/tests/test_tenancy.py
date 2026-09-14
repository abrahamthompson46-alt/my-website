from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.services.email import get_or_create_security_profile
from customer_portal.models import Subscription
from customer_portal.models.subscription import SubscriptionStatus
from organizations.models import MembershipRole, Organization
from organizations.services import (
    ACTIVE_ORG_SESSION_KEY,
    add_member,
    create_organization,
    ensure_default_organization,
    set_active_organization,
)
from products.models import Product, ProductCategory, ProductStatus


User = get_user_model()


class OrganizationServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="SecurePass123!",
        )
        self.member = User.objects.create_user(
            username="member",
            email="member@example.com",
            password="SecurePass123!",
        )

    def test_ensure_default_organization_creates_owner_membership(self):
        org = ensure_default_organization(self.owner, company="Acme Chapel")
        self.assertEqual(org.name, "Acme Chapel")
        membership = org.memberships.get(user=self.owner)
        self.assertEqual(membership.role, MembershipRole.OWNER)

    def test_ensure_default_organization_is_idempotent(self):
        first = ensure_default_organization(self.owner)
        second = ensure_default_organization(self.owner)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Organization.objects.filter(memberships__user=self.owner).count(), 1)

    def test_member_cannot_access_other_org_via_switch(self):
        org_a = create_organization(name="Org A", created_by=self.owner)
        org_b = create_organization(name="Org B", created_by=self.member)
        request = type("Req", (), {"user": self.member, "session": {}})()
        self.assertFalse(set_active_organization(request, org_a))
        self.assertTrue(set_active_organization(request, org_b))


class OrganizationIsolationTests(TestCase):
    def setUp(self):
        self.owner_a = User.objects.create_user(
            username="ownera",
            email="a@example.com",
            password="SecurePass123!",
        )
        self.owner_b = User.objects.create_user(
            username="ownerb",
            email="b@example.com",
            password="SecurePass123!",
        )
        for user in (self.owner_a, self.owner_b):
            profile = get_or_create_security_profile(user)
            profile.email_verified = True
            profile.save(update_fields=["email_verified", "updated_at"])

        self.org_a = ensure_default_organization(self.owner_a, company="Alpha Org")
        self.org_b = ensure_default_organization(self.owner_b, company="Beta Org")
        category = ProductCategory.objects.create(name="Vertical", slug="vertical")
        self.product = Product.objects.create(
            name="ChurchHub",
            slug="churchhub",
            category=category,
            is_published=True,
            status=ProductStatus.GA,
        )
        self.sub_a = Subscription.objects.create(
            user=self.owner_a,
            product=self.product,
            plan_name="Starter",
            status=SubscriptionStatus.TRIAL,
            amount=0,
            currency="GHS",
            started_at="2026-01-01",
            organization=self.org_a,
        )
        self.sub_b = Subscription.objects.create(
            user=self.owner_b,
            product=self.product,
            plan_name="Starter",
            status=SubscriptionStatus.TRIAL,
            amount=0,
            currency="GHS",
            started_at="2026-01-01",
            organization=self.org_b,
        )
        self.client = Client()

    def test_portal_lists_only_active_organization_subscriptions(self):
        self.client.force_login(self.owner_a)
        session = self.client.session
        session[ACTIVE_ORG_SESSION_KEY] = str(self.org_a.pk)
        session.save()

        response = self.client.get(reverse("customer_portal:subscriptions"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Alpha Org", content)
        self.assertContains(response, "Starter")
        # Ensure we are not leaking the other tenant's org name via shared product alone —
        # isolation is by queryset; other org's subscription must not appear as a second row.
        self.assertEqual(
            list(response.context["object_list"]),
            [self.sub_a],
        )

    def test_cross_org_member_sees_shared_org_data(self):
        add_member(organization=self.org_a, user=self.owner_b, role=MembershipRole.MEMBER)
        self.client.force_login(self.owner_b)
        session = self.client.session
        session[ACTIVE_ORG_SESSION_KEY] = str(self.org_a.pk)
        session.save()

        response = self.client.get(reverse("customer_portal:subscriptions"))
        self.assertEqual(list(response.context["object_list"]), [self.sub_a])

    def test_switch_rejects_foreign_organization(self):
        self.client.force_login(self.owner_a)
        response = self.client.post(
            reverse("customer_portal:organization_switch"),
            {"organization_id": str(self.org_b.pk)},
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(self.client.session.get(ACTIVE_ORG_SESSION_KEY), str(self.org_b.pk))
