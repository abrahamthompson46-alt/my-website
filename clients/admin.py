from django.contrib import admin

from clients.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "client_number",
        "display_name",
        "client_type",
        "status",
        "organization",
        "phone",
        "city",
        "created_at",
    )
    list_filter = ("status", "client_type", "country")
    search_fields = (
        "client_number",
        "display_name",
        "first_name",
        "last_name",
        "phone",
        "email",
        "national_id",
        "external_reference",
        "organization__name",
        "organization__slug",
    )
    autocomplete_fields = ("organization", "created_by")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("organization", "client_number")
