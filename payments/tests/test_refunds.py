from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import AuditEventType, AuditLog
from payments.constants import MANUAL
from payments.models import GatewayConfiguration, Payment, PaymentStatus, RefundStatus
from payments.services.refunds import create_refund


User = get_user_model()


class RefundSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer@example.com",
            email="buyer@example.com",
            password="SecurePass123!",
        )
        self.staff = User.objects.create_user(
            username="staff@example.com",
            email="staff@example.com",
            password="SecurePass123!",
            is_staff=True,
        )
        self.gateway = GatewayConfiguration.objects.create(
            code=MANUAL,
            name="Manual",
            is_active=True,
            is_default=True,
        )
        self.payment = Payment.objects.create(
            user=self.user,
            gateway=self.gateway,
            reference="PAY-REFUND-1",
            amount=Decimal("100.00"),
            currency="GHS",
            status=PaymentStatus.SUCCEEDED,
            idempotency_key="idem-refund-1",
        )

    def test_full_refund_marks_payment_refunded_and_audits(self):
        refund, result = create_refund(
            self.payment,
            amount=Decimal("100.00"),
            reason="Customer request",
            initiated_by=self.staff,
        )
        self.assertTrue(result.success)
        self.assertEqual(refund.status, RefundStatus.SUCCEEDED)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, PaymentStatus.REFUNDED)
        self.assertTrue(
            AuditLog.objects.filter(
                event_type=AuditEventType.PAYMENT_REFUNDED,
                metadata__refund_reference=refund.reference,
            ).exists()
            or AuditLog.objects.filter(event_type=AuditEventType.PAYMENT_REFUNDED).exists()
        )

    def test_partial_refund_marks_partially_refunded(self):
        create_refund(self.payment, amount=Decimal("40.00"), initiated_by=self.staff)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, PaymentStatus.PARTIALLY_REFUNDED)

    def test_rejects_refund_above_refundable_amount(self):
        create_refund(self.payment, amount=Decimal("60.00"), initiated_by=self.staff)
        with self.assertRaises(ValueError):
            create_refund(self.payment, amount=Decimal("50.00"), initiated_by=self.staff)

    def test_rejects_zero_and_negative_refunds(self):
        with self.assertRaises(ValueError):
            create_refund(self.payment, amount=Decimal("0.00"), initiated_by=self.staff)
        with self.assertRaises(ValueError):
            create_refund(self.payment, amount=Decimal("-1.00"), initiated_by=self.staff)

    def test_rejects_refund_on_pending_payment(self):
        pending = Payment.objects.create(
            user=self.user,
            gateway=self.gateway,
            reference="PAY-REFUND-PENDING",
            amount=Decimal("50.00"),
            currency="GHS",
            status=PaymentStatus.PENDING,
            idempotency_key="idem-refund-pending",
        )
        with self.assertRaises(ValueError):
            create_refund(pending, amount=Decimal("10.00"), initiated_by=self.staff)
