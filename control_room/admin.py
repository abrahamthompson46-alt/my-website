from django.contrib import admin

from control_room.models import (
    ControlChangeLog,
    FeatureFlag,
    NavigationMenu,
    PlatformSettings,
    RedirectRule,
    SiteAnnouncement,
)


@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    list_display = ("site_name", "maintenance_mode", "updated_at")


@admin.register(NavigationMenu)
class NavigationMenuAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "updated_at")
    search_fields = ("code", "name")


@admin.register(RedirectRule)
class RedirectRuleAdmin(admin.ModelAdmin):
    list_display = ("from_path", "to_path", "to_url_name", "redirect_type", "is_active")
    list_filter = ("is_active", "redirect_type")


@admin.register(SiteAnnouncement)
class SiteAnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "variant", "is_active", "show_on_public", "starts_at", "ends_at")
    list_filter = ("variant", "is_active", "show_on_public")


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ("label", "key", "is_enabled")
    list_filter = ("is_enabled",)


@admin.register(ControlChangeLog)
class ControlChangeLogAdmin(admin.ModelAdmin):
    list_display = ("area", "action", "summary", "user", "created_at")
    list_filter = ("area", "action")
    readonly_fields = ("user", "area", "action", "summary", "details", "created_at")
