from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

import pyotp

from accounts.models import MFAMethod
from accounts.services.email import get_or_create_security_profile
from accounts.services.mfa import enable_totp, generate_backup_codes, generate_totp_secret

User = get_user_model()


class AuthFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user@test.com",
            email="user@test.com",
            password="SecurePass123!",
        )
        get_or_create_security_profile(self.user).mark_email_verified()

    def test_login_redirects_to_portal(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "user@test.com", "password": "SecurePass123!"},
        )
        self.assertRedirects(response, reverse("customer_portal:dashboard"))

    def test_logout_requires_post(self):
        self.client.login(username="user@test.com", password="SecurePass123!")
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)

    def test_logout_shows_signed_out_page(self):
        self.client.login(username="user@test.com", password="SecurePass123!")
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:logged_out"))

    def test_logged_out_page_renders(self):
        response = self.client.get(reverse("accounts:logged_out"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "signed out", status_code=200)

    def test_staff_login_redirects_to_control_room(self):
        secret = generate_totp_secret()
        _, hashed = generate_backup_codes(count=2)
        self.user.is_staff = True
        self.user.save()
        enable_totp(self.user, secret, hashed)

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "user@test.com", "password": "SecurePass123!"},
        )
        self.assertRedirects(response, reverse("accounts:mfa_verify"))

        code = pyotp.TOTP(secret).now()
        response = self.client.post(reverse("accounts:mfa_verify"), {"code": code})
        self.assertRedirects(response, reverse("control_room:dashboard"))

    def test_mfa_disable_requires_code(self):
        secret = generate_totp_secret()
        _, hashed = generate_backup_codes(count=2)
        enable_totp(self.user, secret, hashed)
        self.client.login(username="user@test.com", password="SecurePass123!")

        response = self.client.post(
            reverse("accounts:mfa_disable"),
            {"password": "SecurePass123!", "code": ""},
        )
        self.assertRedirects(response, reverse("customer_portal:security"))
        profile = get_or_create_security_profile(self.user)
        self.assertTrue(profile.mfa_enabled)

    def test_mfa_login_flow(self):
        secret = generate_totp_secret()
        _, hashed = generate_backup_codes(count=2)
        enable_totp(self.user, secret, hashed)

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "user@test.com", "password": "SecurePass123!"},
        )
        self.assertRedirects(response, reverse("accounts:mfa_verify"))

        code = pyotp.TOTP(secret).now()
        response = self.client.post(reverse("accounts:mfa_verify"), {"code": code})
        self.assertRedirects(response, reverse("customer_portal:dashboard"))
