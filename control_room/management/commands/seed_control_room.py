from django.core.management.base import BaseCommand

from common import navigation as nav_constants
from control_room.models import FeatureFlag, NavigationMenu, PlatformSettings
from control_room.services import invalidate_navigation_cache, invalidate_platform_settings_cache


class Command(BaseCommand):
    help = "Seed control room with default platform settings, navigation menus, and feature flags."

    def handle(self, *args, **options):
        PlatformSettings.load()
        self.stdout.write("Platform settings ready.")

        menus = [
            ("public_header", "Public header", nav_constants.PUBLIC_HEADER_NAV),
            ("public_footer", "Public footer", nav_constants.PUBLIC_FOOTER_COLUMNS),
            ("customer_portal", "Customer portal", nav_constants.CUSTOMER_PORTAL_NAV),
            ("operations", "Operations", nav_constants.OPERATIONS_NAV),
            ("partner_portal", "Partner portal", nav_constants.PARTNER_PORTAL_NAV),
            ("control_room", "Control room", nav_constants.CONTROL_ROOM_NAV),
        ]
        for code, name, structure in menus:
            menu, created = NavigationMenu.objects.update_or_create(
                code=code,
                defaults={"name": name, "structure": structure, "is_active": True},
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} navigation menu: {code} ({len(structure)} items)")

        default_flags = [
            ("demo_form", "Demo request form", "Show demo request forms on marketing pages", True),
            ("newsletter", "Newsletter signup", "Show newsletter capture forms", True),
            ("partner_program", "Partner program", "Enable partner portal and partner CTAs", True),
            ("public_registration", "Public registration", "Allow self-service account registration", False),
        ]
        for key, label, description, enabled in default_flags:
            FeatureFlag.objects.update_or_create(
                key=key,
                defaults={"label": label, "description": description, "is_enabled": enabled},
            )
            self.stdout.write(f"Feature flag ready: {key}")

        invalidate_platform_settings_cache()
        invalidate_navigation_cache()
        self.stdout.write(self.style.SUCCESS("Control room seed complete."))
