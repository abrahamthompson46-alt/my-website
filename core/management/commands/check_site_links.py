"""
Validate named routes and navigation links used across the site.
Usage: python manage.py check_site_links
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.test import Client, override_settings
from django.urls import NoReverseMatch, reverse

from accounts.services.email import get_or_create_security_profile
from common import navigation as nav
from common.navigation import CONTROL_ROOM_NAV
from products.models import Product

User = get_user_model()


def _collect_nav_links(structure):
    links = []
    for item in structure:
        if item.get("url_name"):
            links.append(
                {
                    "label": item.get("label", item.get("title", "?")),
                    "url_name": item["url_name"],
                    "url_kwargs": item.get("url_kwargs"),
                }
            )
        for column in item.get("columns", []):
            for link in column.get("links", []):
                if link.get("url_name"):
                    links.append(
                        {
                            "label": link.get("label", "?"),
                            "url_name": link["url_name"],
                            "url_kwargs": link.get("url_kwargs"),
                        }
                    )
    return links


class Command(BaseCommand):
    help = "Verify navigation and core public routes resolve and return success status codes."

    def handle(self, *args, **options):
        client = Client()
        reverse_errors = []
        http_errors = []

        with override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"]):
            self._check_links(client, reverse_errors, http_errors)
            self._check_staff_links(client, reverse_errors, http_errors)

        if reverse_errors:
            self.stdout.write(self.style.ERROR("ROUTE ERRORS:"))
            for item in reverse_errors:
                self.stdout.write(f"  x {item}")

        if http_errors:
            self.stdout.write(self.style.ERROR("HTTP ERRORS:"))
            for item in http_errors:
                self.stdout.write(f"  x {item}")

        if not reverse_errors and not http_errors:
            self.stdout.write(self.style.SUCCESS("All checked links passed."))
        else:
            self.stdout.write(self.style.ERROR("Fix broken links before go-live."))

    def _check_links(self, client, reverse_errors, http_errors):

        core_routes = [
            ("website:home", {}),
            ("website:privacy", {}),
            ("website:terms", {}),
            ("website:security", {}),
            ("website:refund", {}),
            ("website:status", {}),
            ("products:list", {}),
            ("products:detail", {"slug": "churchhub"}),
            ("products:pricing", {"slug": "churchhub"}),
            ("products:plan_start", {"slug": "churchhub"}),
            ("products:compare", {}),
            ("contact:form", {}),
            ("contact:trial", {}),
            ("contact:demo", {}),
            ("pages:about", {}),
            ("pages:list", {}),
            ("documentation:index", {}),
            ("support:index", {}),
            ("careers:list", {}),
            ("marketing:blog_list", {}),
            ("marketing:events", {}),
            ("marketing:case_studies", {}),
            ("marketing:whitepapers", {}),
            ("marketing:resources", {}),
            ("marketing:success_stories", {}),
            ("accounts:login", {}),
            ("accounts:register", {}),
            ("control_room:dashboard", {}),
            ("control_room:products", {}),
            ("control_room:changelog", {}),
            ("control_room:redirects", {}),
            ("control_room:announcements", {}),
            ("control_room:navigation", {}),
            ("control_room:flags", {}),
            ("control_room:content", {}),
            ("control_room:documentation", {}),
            ("control_room:doc_articles", {}),
            ("control_room:doc_videos", {}),
            ("control_room:doc_downloads", {}),
            ("control_room:doc_categories", {}),
            ("control_room:team", {}),
            ("control_room:settings", {}),
            ("control_room:setup", {}),
            ("control_room:product_create", {}),
            ("operations:dashboard", {}),
            ("operations:demo_requests", {}),
            ("operations:customers", {}),
            ("operations:payments", {}),
            ("operations:support", {}),
            ("operations:activity", {}),
            ("operations:system_health", {}),
        ]

        nav_links = _collect_nav_links(nav.PUBLIC_HEADER_NAV)
        nav_links += _collect_nav_links(nav.PUBLIC_FOOTER_COLUMNS)

        seen = set()
        for label, url_name, url_kwargs in [
            (f"core:{name}", name, kwargs) for name, kwargs in core_routes
        ] + [(link["label"], link["url_name"], link.get("url_kwargs")) for link in nav_links]:
            key = (url_name, tuple(sorted((url_kwargs or {}).items())))
            if key in seen:
                continue
            seen.add(key)
            try:
                path = reverse(url_name, kwargs=url_kwargs or {})
            except NoReverseMatch as exc:
                reverse_errors.append(f"{label} -> {url_name}: {exc}")
                continue

            response = client.get(path, follow=False)
            # Staff-only routes redirect to login when anonymous.
            if response.status_code >= 400 and response.status_code not in {302, 403}:
                http_errors.append(f"{label} -> {path} returned HTTP {response.status_code}")

        return len(reverse_errors) + len(http_errors)

    def _check_staff_links(self, client, reverse_errors, http_errors):
        user, _ = User.objects.get_or_create(
            email="link-checker@example.com",
            defaults={
                "username": "link-checker",
                "is_staff": True,
            },
        )
        user.is_staff = True
        user.set_password("link-checker-pass")
        user.save(update_fields=["is_staff", "password"])

        profile = get_or_create_security_profile(user)
        profile.email_verified = True
        profile.mfa_enabled = True
        profile.save(update_fields=["email_verified", "mfa_enabled"])

        client.force_login(user)

        staff_routes = [
            ("control_room:products", {}),
            ("control_room:changelog", {}),
            ("control_room:redirects", {}),
            ("control_room:announcements", {}),
            ("control_room:navigation", {}),
            ("control_room:flags", {}),
            ("control_room:content", {}),
            ("control_room:settings", {}),
            ("control_room:setup", {}),
            ("control_room:product_create", {}),
            ("operations:dashboard", {}),
            ("operations:demo_requests", {}),
            ("operations:customers", {}),
            ("operations:payments", {}),
            ("operations:support", {}),
            ("operations:activity", {}),
        ]

        for item in CONTROL_ROOM_NAV:
            if item.get("section") or item.get("external"):
                continue
            if item["url_name"] == "control_room:team":
                continue
            staff_routes.append((item["url_name"], item.get("url_kwargs") or {}))

        product = Product.objects.filter(slug="churchhub").first()
        if product:
            staff_routes.extend(
                [
                    ("control_room:product_detail", {"pk": product.pk}),
                    ("control_room:product_edit", {"pk": product.pk}),
                    ("control_room:product_pricing", {"pk": product.pk}),
                ]
            )

        seen = set()
        for url_name, url_kwargs in staff_routes:
            key = (url_name, tuple(sorted(url_kwargs.items())))
            if key in seen:
                continue
            seen.add(key)

            label = f"staff:{url_name}"
            try:
                path = reverse(url_name, kwargs=url_kwargs)
            except NoReverseMatch as exc:
                reverse_errors.append(f"{label} -> {url_name}: {exc}")
                continue

            response = client.get(path, follow=False)
            if response.status_code >= 400:
                http_errors.append(f"{label} -> {path} returned HTTP {response.status_code}")
