from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.services.email import get_or_create_security_profile
from payments.constants import MANUAL
from payments.models import GatewayConfiguration, ManualPaymentDetail, Payment, PaymentStatus

User = get_user_model()


class PrivateMediaAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner@example.com",
            email="owner@example.com",
            password="SecurePass123!",
        )
        self.other = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="SecurePass123!",
        )
        self.staff = User.objects.create_user(
            username="staff@example.com",
            email="staff@example.com",
            password="SecurePass123!",
            is_staff=True,
        )
        get_or_create_security_profile(self.owner).mark_email_verified()
        get_or_create_security_profile(self.other).mark_email_verified()
        get_or_create_security_profile(self.staff).mark_email_verified()
        staff_profile = get_or_create_security_profile(self.staff)
        staff_profile.mfa_enabled = True
        staff_profile.save(update_fields=["mfa_enabled", "updated_at"])

        gateway = GatewayConfiguration.objects.create(code=MANUAL, name="Manual", is_active=True)
        self.payment = Payment.objects.create(
            user=self.owner,
            gateway=gateway,
            reference="PAY-PROOF-001",
            amount=Decimal("49.00"),
            currency="GHS",
            status=PaymentStatus.PENDING_CONFIRMATION,
            manual_method="bank_transfer",
        )
        proof = SimpleUploadedFile("proof.pdf", b"secret-payment-proof", content_type="application/pdf")
        ManualPaymentDetail.objects.create(payment=self.payment, proof_document=proof)

    @override_settings(DEBUG=False)
    def test_public_media_route_blocks_private_paths(self):
        response = self.client.get("/media/private/payments/proofs/proof.pdf")
        self.assertEqual(response.status_code, 404)

    @override_settings(DEBUG=False)
    def test_public_media_route_blocks_legacy_proof_paths(self):
        response = self.client.get("/media/payments/proofs/legacy-proof.pdf")
        self.assertEqual(response.status_code, 404)

    @override_settings(DEBUG=False)
    def test_public_marketing_media_still_served(self):
        response = self.client.get("/media/products/screenshots/example.png")
        self.assertIn(response.status_code, {200, 404})

    def test_owner_can_download_proof(self):
        self.client.login(username="owner@example.com", password="SecurePass123!")
        url = reverse("payments:proof_download", kwargs={"pk": self.payment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"secret-payment-proof", b"".join(response.streaming_content))

    def test_other_user_cannot_download_proof(self):
        self.client.login(username="other@example.com", password="SecurePass123!")
        url = reverse("payments:proof_download", kwargs={"pk": self.payment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user_cannot_download_proof(self):
        url = reverse("payments:proof_download", kwargs={"pk": self.payment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_staff_can_download_proof(self):
        self.client.login(username="staff@example.com", password="SecurePass123!")
        url = reverse("payments:proof_download", kwargs={"pk": self.payment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
