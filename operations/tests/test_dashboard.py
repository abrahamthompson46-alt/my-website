from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from accounts.services.email import get_or_create_security_profile


class OperationsDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ops-staff",
            email="ops-staff@example.com",
            password="testpass123",
            is_staff=True,
        )
        profile = get_or_create_security_profile(self.user)
        profile.email_verified = True
        profile.mfa_enabled = True
        profile.save(update_fields=["email_verified", "mfa_enabled"])
        self.client.force_login(self.user)

    def test_ops_dashboard_shows_cedi_revenue(self):
        response = self.client.get(reverse("operations:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Revenue (30d)")
        self.assertContains(response, "GH\u20b50")
        self.assertNotContains(response, "$0")
