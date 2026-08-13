"""Tests ensuring web-triggered deployment cannot execute shell commands."""

import importlib
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User
from accounts.services.email import get_or_create_security_profile
from accounts.services.rbac import assign_role
from control_room.models import ControlChangeLog


class WebDeploySecurityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="pass",
            is_staff=True,
        )
        owner_role = Role.objects.create(name="Platform Owner", slug="platform-owner")
        assign_role(self.owner, owner_role)
        profile = get_or_create_security_profile(self.owner)
        profile.email_verified = True
        profile.mfa_enabled = True
        profile.save(update_fields=["email_verified", "mfa_enabled"])
        self.client.force_login(self.owner)

    def test_deploy_service_module_removed(self):
        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("control_room.services.deploy")

    def test_platform_ops_page_does_not_offer_web_deploy(self):
        response = self.client.get(reverse("control_room:platform_ops"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Web-triggered deployment is disabled", content)
        self.assertNotIn("Pull latest from GitHub", content)
        self.assertNotIn('name="action" value="deploy"', content)

    @patch("subprocess.run")
    def test_deploy_post_does_not_execute_subprocess(self, mock_run):
        response = self.client.post(
            reverse("control_room:platform_ops"),
            {
                "action": "deploy",
                "git_remote": "origin",
                "git_branch": "main",
                "confirm_deploy": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        mock_run.assert_not_called()

        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertTrue(any("disabled for security" in message for message in messages))

        log = ControlChangeLog.objects.filter(action="deploy_blocked").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.area, "platform_ops")

    @patch("subprocess.run")
    def test_no_subprocess_on_platform_ops_email_actions(self, mock_run):
        self.client.post(
            reverse("control_room:platform_ops"),
            {
                "action": "save_email",
                "use_custom_smtp": "on",
                "smtp_host": "smtp.example.com",
                "smtp_port": "587",
                "smtp_use_tls": "on",
                "smtp_username": "mailer",
                "default_from_email": "noreply@example.com",
            },
        )
        mock_run.assert_not_called()
