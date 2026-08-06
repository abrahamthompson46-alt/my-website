from django.contrib import admin

from customer_portal.models import (
    CustomerDownload,
    CustomerProfile,
    Invoice,
    License,
    PortalNotification,
    ProductUpdate,
    Subscription,
    SupportTicket,
    TicketMessage,
)


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "plan_name", "status", "renews_at", "amount")
    list_filter = ("status", "billing_interval", "product")
    search_fields = ("user__email", "product__name", "plan_name")


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "license_key", "status", "seats", "expires_at")
    list_filter = ("status", "product")
    search_fields = ("user__email", "license_key", "product__name")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "user", "amount", "currency", "status", "issued_at", "due_at")
    list_filter = ("status", "currency")
    search_fields = ("invoice_number", "user__email")


@admin.register(CustomerDownload)
class CustomerDownloadAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "product", "category", "version", "is_active")
    list_filter = ("category", "is_active", "product")
    search_fields = ("title", "user__email")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "subject", "status", "priority", "created_at")
    list_filter = ("status", "priority", "product")
    search_fields = ("reference", "subject", "user__email")
    inlines = [TicketMessageInline]


@admin.register(ProductUpdate)
class ProductUpdateAdmin(admin.ModelAdmin):
    list_display = ("product", "title", "version", "update_type", "published_at", "is_published")
    list_filter = ("update_type", "is_published", "product")
    search_fields = ("title", "version", "product__name")


@admin.register(PortalNotification)
class PortalNotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "notification_type", "is_read", "created_at")
    list_filter = ("notification_type", "is_read")
    search_fields = ("title", "user__email")


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "job_title", "country", "timezone")
    search_fields = ("user__email", "company")
