"""Tests for Celery async dispatch helpers and tasks."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings

from common.services.async_jobs import celery_async_enabled, dispatch_task
from common.tasks import process_webhook_task, send_platform_mail_task
from config.celery_settings import derive_celery_broker_url
from payments.gateways.dto import WebhookResult
from payments.models import GatewayConfiguration, Payment, PaymentStatus
from payments.services.webhooks import enqueue_process_webhook

User = get_user_model()


class CeleryBrokerUrlTests(TestCase):
    def test_explicit_broker_wins(self):
        self.assertEqual(
            derive_celery_broker_url("redis://localhost:6379/0", "redis://broker:6379/2"),
            "redis://broker:6379/2",
        )

    def test_derives_db_1_from_redis_db_0(self):
        self.assertEqual(
            derive_celery_broker_url("redis://localhost:6379/0"),
            "redis://localhost:6379/1",
        )

    def test_memory_fallback_without_redis(self):
        self.assertEqual(derive_celery_broker_url(None), "memory://")


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_BROKER_URL="memory://")
class AsyncDispatchTests(TestCase):
    def test_celery_async_disabled_when_eager(self):
        self.assertFalse(celery_async_enabled())

    def test_queue_platform_mail_sends_inline_in_tests(self):
        from control_room.services.email_delivery import queue_platform_mail

        queue_platform_mail(
            subject="Hello",
            message="Body",
            recipient_list=["user@example.com"],
            html_message="<p>Body</p>",
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Hello")
        self.assertEqual(mail.outbox[0].to, ["user@example.com"])

    def test_send_platform_mail_task_runs(self):
        send_platform_mail_task(
            subject="Task mail",
            message="Hi",
            recipient_list=["task@example.com"],
        )
        self.assertEqual(len(mail.outbox), 1)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_BROKER_URL="memory://")
class WebhookEnqueueTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="async@test.com",
            email="async@test.com",
            password="testpass123",
        )
        self.gateway = GatewayConfiguration.objects.create(
            code="paystack",
            name="Paystack",
            is_active=True,
            settings={"enabled": True, "secret_key": "sk_test"},
        )
        self.payment = Payment.objects.create(
            user=self.user,
            gateway=self.gateway,
            reference="PAY-ASYNC-001",
            gateway_reference="GW-ASYNC",
            amount=Decimal("50.00"),
            currency="GHS",
            status=PaymentStatus.PENDING,
            customer_email="async@test.com",
        )

    def test_enqueue_runs_inline_when_eager(self):
        payload = {
            "event": "charge.success",
            "data": {"reference": self.payment.reference, "amount": 5000, "currency": "GHS", "id": "evt_async_1"},
        }
        adapter = MagicMock()
        adapter.supports_webhooks = True
        adapter.verify_webhook.return_value = True
        adapter.parse_webhook.return_value = WebhookResult(
            handled=True,
            event_type="charge.success",
            reference=self.payment.reference,
            gateway_reference="GW-ASYNC",
            status="succeeded",
            amount=Decimal("5000"),
            currency="GHS",
            raw_payload=payload,
        )

        with patch("payments.services.webhooks.get_gateway_from_model", return_value=adapter):
            event, created = enqueue_process_webhook(self.gateway, payload, b"{}", {})

        self.assertTrue(created)
        self.assertIsNotNone(event)
        self.assertTrue(event.processed)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, PaymentStatus.SUCCEEDED)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=False, CELERY_BROKER_URL="redis://localhost:6379/1")
    def test_enqueue_queues_when_async_enabled(self):
        with patch("common.services.async_jobs.dispatch_task") as mock_dispatch:
            event, queued = enqueue_process_webhook(self.gateway, {"id": "x"}, b"{}", {})

        self.assertIsNone(event)
        self.assertTrue(queued)
        mock_dispatch.assert_called_once()
        self.assertEqual(mock_dispatch.call_args.args[0], process_webhook_task)


@override_settings(CELERY_TASK_ALWAYS_EAGER=False, CELERY_BROKER_URL="redis://localhost:6379/1")
class DispatchTaskTests(TestCase):
    def test_dispatch_uses_delay_when_async(self):
        task = MagicMock()
        task.delay.return_value = "queued"
        result = dispatch_task(task, 1, foo="bar")
        self.assertEqual(result, "queued")
        task.delay.assert_called_once_with(1, foo="bar")
