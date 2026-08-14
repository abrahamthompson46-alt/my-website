from django.test import TestCase
from django.urls import reverse

import pyotp

from accounts.models import MFAMethod
from accounts.services.email import get_or_create_security_profile
from accounts.services.mfa import (
    disable_mfa,
    enable_totp,
    generate_backup_codes,
    generate_totp_secret,
    verify_backup_code,
    verify_mfa_code,
    verify_totp,
)
from accounts.models import User


class MFAServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="mfa-user",
            email="mfa@example.com",
            password="testpass123",
        )

    def test_totp_round_trip(self):
        secret = generate_totp_secret()
        code = pyotp.TOTP(secret).now()
        self.assertTrue(verify_totp(secret, code))
        self.assertFalse(verify_totp(secret, "000000"))

    def test_enable_and_verify_mfa(self):
        secret = generate_totp_secret()
        _, hashed = generate_backup_codes(count=2)
        enable_totp(self.user, secret, hashed)

        profile = get_or_create_security_profile(self.user)
        self.assertTrue(profile.mfa_enabled)
        self.assertEqual(profile.mfa_method, MFAMethod.TOTP)

        code = pyotp.TOTP(secret).now()
        self.assertTrue(verify_mfa_code(profile, code))

    def test_backup_code_single_use(self):
        secret = generate_totp_secret()
        plain, hashed = generate_backup_codes(count=1)
        enable_totp(self.user, secret, hashed)

        profile = get_or_create_security_profile(self.user)
        self.assertTrue(verify_backup_code(profile, plain[0]))
        profile.refresh_from_db()
        self.assertFalse(verify_backup_code(profile, plain[0]))

    def test_disable_mfa_clears_secrets(self):
        secret = generate_totp_secret()
        _, hashed = generate_backup_codes(count=2)
        enable_totp(self.user, secret, hashed)
        disable_mfa(self.user)

        profile = get_or_create_security_profile(self.user)
        self.assertFalse(profile.mfa_enabled)
        self.assertEqual(profile.mfa_method, MFAMethod.NONE)
        self.assertEqual(profile.mfa_secret, "")
        self.assertEqual(profile.backup_codes, [])


class MFAURLTests(TestCase):
    def test_mfa_verify_url_resolves(self):
        self.assertEqual(reverse("accounts:mfa_verify"), "/accounts/mfa/verify/")

    def test_mfa_enroll_requires_login(self):
        response = self.client.get(reverse("accounts:mfa_enroll"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_mfa_enroll_rescan_regenerates_secret(self):
        user = User.objects.create_user(
            username="rescan-user",
            email="rescan@example.com",
            password="testpass123",
        )
        profile = get_or_create_security_profile(user)
        profile.email_verified = True
        profile.save(update_fields=["email_verified"])
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:mfa_enroll"))
        self.assertEqual(response.status_code, 200)
        first_secret = response.context["secret"]

        response = self.client.get(reverse("accounts:mfa_enroll"), {"rescan": "1"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:mfa_enroll"))

        response = self.client.get(reverse("accounts:mfa_enroll"))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.context["secret"], first_secret)

    def test_mfa_verify_rescan_is_not_available_during_login_challenge(self):
        user = User.objects.create_user(
            username="verify-rescan",
            email="verify-rescan@example.com",
            password="testpass123",
        )
        secret = generate_totp_secret()
        _, hashed = generate_backup_codes(count=2)
        enable_totp(user, secret, hashed)

        session = self.client.session
        session["mfa_pending_user_id"] = str(user.pk)
        session.save()

        response = self.client.get(reverse("accounts:mfa_verify"), {"rescan": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("rescan_mode", response.context)
        self.assertNotIn("qr_data_uri", response.context)
        self.assertNotIn("mfa_rescan_secret", self.client.session)

    def test_mfa_verify_rescan_cannot_replace_totp_during_post(self):
        user = User.objects.create_user(
            username="verify-post-rescan",
            email="verify-post-rescan@example.com",
            password="testpass123",
        )
        original_secret = generate_totp_secret()
        _, hashed = generate_backup_codes(count=2)
        enable_totp(user, original_secret, hashed)

        session = self.client.session
        session["mfa_pending_user_id"] = str(user.pk)
        session["mfa_rescan_secret"] = generate_totp_secret()
        session.save()

        import pyotp

        new_secret = session["mfa_rescan_secret"]
        code = pyotp.TOTP(new_secret).now()
        response = self.client.post(reverse("accounts:mfa_verify"), {"code": code})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

        profile = get_or_create_security_profile(user)
        self.assertEqual(profile.mfa_secret, original_secret)
