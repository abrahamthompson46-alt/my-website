"""Security regression tests for invitation acceptance."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Role
from accounts.services.email import get_or_create_security_profile
from accounts.services.invitations import create_staff_invitation
from accounts.services.mfa import enable_totp, generate_backup_codes, generate_totp_secret

User = get_user_model()


class InvitationSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.inviter = User.objects.create_user(
            username="inviter",
            email="inviter@example.com",
            password="pass",
            is_staff=True,
        )
        self.role = Role.objects.create(name="Platform Admin", slug="platform-admin")

    def _create_invitation(self, email):
        return create_staff_invitation(
            email=email,
            role=self.role,
            invited_by=self.inviter,
            grant_staff_access=True,
        )

    def test_new_user_can_accept_and_is_logged_in(self):
        invitation, raw = self._create_invitation("newuser@example.com")
        url = reverse("accounts:accept_invite", kwargs={"token": raw})
        response = self.client.post(
            url,
            {
                "first_name": "New",
                "last_name": "User",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="newuser@example.com")
        self.assertTrue(user.is_staff)
        self.assertEqual(self.client.session.get("_auth_user_id"), str(user.pk))

    def test_existing_user_cannot_be_logged_in_by_token_alone(self):
        existing = User.objects.create_user(
            username="existing",
            email="existing@example.com",
            password="ExistingPass123!",
            is_staff=True,
        )
        _, raw = self._create_invitation("existing@example.com")
        url = reverse("accounts:accept_invite", kwargs={"token": raw})
        response = self.client.post(url, {"accept_existing": "1"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
        self.assertNotIn("_auth_user_id", self.client.session)
        existing.refresh_from_db()
        self.assertTrue(existing.user_roles.filter(role=self.role).exists())

    def test_existing_user_already_authenticated_can_accept_in_place(self):
        existing = User.objects.create_user(
            username="signedin",
            email="signedin@example.com",
            password="SignedInPass123!",
            is_staff=True,
        )
        self.client.login(username="signedin@example.com", password="SignedInPass123!")
        _, raw = self._create_invitation("signedin@example.com")
        url = reverse("accounts:accept_invite", kwargs={"token": raw})
        response = self.client.post(url, {"accept_existing": "1"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get("_auth_user_id"), str(existing.pk))
        existing.refresh_from_db()
        self.assertTrue(existing.user_roles.filter(role=self.role).exists())

    def test_existing_user_with_mfa_must_sign_in_after_acceptance(self):
        existing = User.objects.create_user(
            username="mfauser",
            email="mfauser@example.com",
            password="MfaPass123!",
            is_staff=True,
        )
        secret = generate_totp_secret()
        _, hashed = generate_backup_codes(count=2)
        enable_totp(existing, secret, hashed)
        _, raw = self._create_invitation("mfauser@example.com")
        url = reverse("accounts:accept_invite", kwargs={"token": raw})
        response = self.client.post(url, {"accept_existing": "1"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_invalid_token_shows_invalid_page(self):
        response = self.client.get(reverse("accounts:accept_invite", kwargs={"token": "not-a-valid-token"}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "invalid", status_code=200)

    def test_expired_invitation_cannot_be_accepted(self):
        invitation, raw = self._create_invitation("expired@example.com")
        invitation.status = "expired"
        invitation.save(update_fields=["status"])
        url = reverse("accounts:accept_invite", kwargs={"token": raw})
        response = self.client.post(
            url,
            {
                "first_name": "Exp",
                "last_name": "Ired",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
