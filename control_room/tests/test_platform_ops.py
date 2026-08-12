from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User
from accounts.services.email import get_or_create_security_profile
from accounts.services.rbac import assign_role, user_can_manage_platform_ops
from control_room.services.email_delivery import EmailConfigurationError, get_email_status_summary


class PlatformOpsAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="pass",
            is_staff=True,
        )
        self.staff = User.objects.create_user(
            username="staff",
            email="staff@example.com",
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

    def test_owner_can_open_platform_ops(self):
        self.assertTrue(user_can_manage_platform_ops(self.owner))
        self.client.force_login(self.owner)
        response = self.client.get(reverse("control_room:platform_ops"))
        self.assertEqual(response.status_code, 200)

    def test_regular_staff_cannot_open_platform_ops(self):
        self.assertFalse(user_can_manage_platform_ops(self.staff))
        self.client.force_login(self.staff)
        response = self.client.get(reverse("control_room:platform_ops"))
        self.assertEqual(response.status_code, 403)


class EmailDeliveryTests(TestCase):
    def test_filebased_backend_without_path_reports_issue(self):
        with self.settings(
            EMAIL_BACKEND="django.core.mail.backends.filebased.EmailBackend",
            EMAIL_FILE_PATH=None,
            DEFAULT_FROM_EMAIL="noreply@example.com",
        ):
            summary = get_email_status_summary()
            self.assertFalse(summary["configured"])
            self.assertIn("EMAIL_FILE_PATH", summary["issues"][0])

    def test_missing_from_email_raises_clear_error(self):
        with self.settings(DEFAULT_FROM_EMAIL=""):
            from control_room.services.email_delivery import send_platform_mail

            with self.assertRaises(EmailConfigurationError):
                send_platform_mail(
                    subject="Test",
                    message="Body",
                    recipient_list=["test@example.com"],
                )
