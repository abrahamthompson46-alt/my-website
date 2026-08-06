"""One-click platform seed / bootstrap runners."""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO

from django.core.management import call_command, get_commands


@dataclass(frozen=True)
class SeedCommand:
    key: str
    command: str
    title: str
    description: str
    icon: str
    group: str
    order: int


SEED_COMMANDS: tuple[SeedCommand, ...] = (
    SeedCommand(
        key="roles",
        command="seed_roles",
        title="Roles & permissions",
        description="Default staff roles and permission groups.",
        icon="shield",
        group="Foundation",
        order=10,
    ),
    SeedCommand(
        key="security_profiles",
        command="ensure_security_profiles",
        title="Security profiles",
        description="Ensure every user has a security profile record.",
        icon="lock",
        group="Foundation",
        order=20,
    ),
    SeedCommand(
        key="control_room",
        command="seed_control_room",
        title="Control room defaults",
        description="Platform settings, navigation menus, and feature flags.",
        icon="sliders",
        group="Platform",
        order=30,
    ),
    SeedCommand(
        key="products",
        command="seed_products",
        title="Product catalog",
        description="Sample products, categories, pricing, and features.",
        icon="package",
        group="Content",
        order=40,
    ),
    SeedCommand(
        key="cms",
        command="seed_cms",
        title="CMS & homepage",
        description="Pages, hero banners, testimonials, FAQs, and team content.",
        icon="layout-dashboard",
        group="Content",
        order=50,
    ),
    SeedCommand(
        key="marketing",
        command="seed_marketing",
        title="Marketing content",
        description="Blog posts, events, case studies, and resources.",
        icon="megaphone",
        group="Content",
        order=60,
    ),
    SeedCommand(
        key="documentation",
        command="seed_documentation",
        title="Documentation",
        description="Doc categories, articles, and API references.",
        icon="book-open",
        group="Content",
        order=70,
    ),
    SeedCommand(
        key="portal",
        command="seed_portal",
        title="Customer portal",
        description="Demo subscriptions, tickets, and portal sample data.",
        icon="users",
        group="Operations",
        order=80,
    ),
    SeedCommand(
        key="payments",
        command="seed_payment_gateways",
        title="Payment gateways",
        description="Default payment gateway configuration records.",
        icon="credit-card",
        group="Operations",
        order=90,
    ),
)


def get_seed_registry() -> list[dict]:
    available = set(get_commands().keys())
    registry = []
    for seed in sorted(SEED_COMMANDS, key=lambda s: s.order):
        registry.append(
            {
                "key": seed.key,
                "command": seed.command,
                "title": seed.title,
                "description": seed.description,
                "icon": seed.icon,
                "group": seed.group,
                "available": seed.command in available,
            }
        )
    return registry


def run_seed_command(command: str) -> dict:
    """Execute a management command and capture output."""
    out = StringIO()
    err = StringIO()
    try:
        call_command(command, stdout=out, stderr=err)
    except Exception as exc:
        return {
            "ok": False,
            "command": command,
            "output": out.getvalue().strip(),
            "error": str(exc),
        }
    error_text = err.getvalue().strip()
    return {
        "ok": not error_text,
        "command": command,
        "output": out.getvalue().strip() or "Completed successfully.",
        "error": error_text,
    }


def run_seed_by_key(key: str) -> dict:
    for seed in SEED_COMMANDS:
        if seed.key == key:
            result = run_seed_command(seed.command)
            result["key"] = seed.key
            result["title"] = seed.title
            return result
    return {"ok": False, "command": key, "key": key, "title": key, "output": "", "error": "Unknown seed action."}


def run_all_seeds() -> list[dict]:
    results = []
    for seed in sorted(SEED_COMMANDS, key=lambda s: s.order):
        results.append({"key": seed.key, "title": seed.title, **run_seed_command(seed.command)})
    return results
