from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import AuditEventType, AuditLog
from accounts.services.audit import log_audit_event


User = get_user_model()


class AppendOnlyAuditLogTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="auditor",
            email="auditor@example.com",
            password="SecurePass123!",
        )

    def test_can_create_audit_log(self):
        log = log_audit_event(AuditEventType.LOGIN_SUCCESS, user=self.user, message="ok")
        self.assertEqual(log.event_type, AuditEventType.LOGIN_SUCCESS)

    def test_cannot_update_audit_log_instance(self):
        log = log_audit_event(AuditEventType.LOGIN_SUCCESS, user=self.user, message="ok")
        log.message = "tampered"
        with self.assertRaises(PermissionError):
            log.save()

    def test_cannot_delete_audit_log_instance(self):
        log = log_audit_event(AuditEventType.LOGIN_SUCCESS, user=self.user, message="ok")
        with self.assertRaises(PermissionError):
            log.delete()

    def test_cannot_queryset_update_or_delete(self):
        log_audit_event(AuditEventType.LOGIN_FAILED, user=self.user, message="fail")
        with self.assertRaises(PermissionError):
            AuditLog.objects.filter(event_type=AuditEventType.LOGIN_FAILED).update(message="x")
        with self.assertRaises(PermissionError):
            AuditLog.objects.filter(event_type=AuditEventType.LOGIN_FAILED).delete()
