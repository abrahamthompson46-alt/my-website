from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings

from accounts.models import Role
from accounts.services.invitations import create_staff_invitation, send_invitation_email
from common.services.email_branding import format_branded_sender, get_deliverability_warnings

User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@zreta.com",
    SITE_URL="https://zreta.com",
    SITE_NAME="Zreta",
    ALLOWED_HOSTS=["zreta.com", "testserver"],
)
class StaffInvitationEmailTests(TestCase):
    def setUp(self):
        self.inviter = User.objects.create_user(
            username="inviter",
            email="owner@zreta.com",
            password="pass",
            first_name="Abraham",
            last_name="Thompson",
            is_staff=True,
        )
        self.role = Role.objects.create(name="Platform Admin", slug="platform-admin")
        self.factory = RequestFactory()

    def test_invitation_email_is_branded_multipart_with_reply_to(self):
        invitation, raw_token = create_staff_invitation(
            email="newmember@example.com",
            role=self.role,
            invited_by=self.inviter,
            message="Welcome aboard — excited to have you on the team.",
        )
        request = self.factory.get("/control/team/")
        request.META["HTTP_HOST"] = "zreta.com"
        request.META["wsgi.url_scheme"] = "https"

        send_invitation_email(request, invitation, raw_token)

        from django.core import mail

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn("team invitation from Abraham Thompson", message.subject)
        self.assertIn("Accept your invitation:", message.body)
        self.assertIn("Welcome aboard", message.body)
        self.assertEqual(len(message.alternatives), 1)
        html, mime = message.alternatives[0]
        self.assertEqual(mime, "text/html")
        self.assertIn("You're invited to the team", html)
        self.assertIn("Accept invitation", html)
        self.assertIn("Platform Admin", html)
        self.assertTrue(message.reply_to)
        self.assertIn("noreply@zreta.com", message.from_email)

    def test_deliverability_warns_on_public_mailbox_domains(self):
        warnings = get_deliverability_warnings("team@gmail.com")
        self.assertTrue(any("gmail.com" in warning for warning in warnings))

    def test_format_branded_sender_includes_display_name(self):
        formatted = format_branded_sender("noreply@zreta.com", "Zreta")
        self.assertIn("Zreta", formatted)
        self.assertIn("noreply@zreta.com", formatted)
