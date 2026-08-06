from django.contrib import admin

from partners.models import PartnerProfile


@admin.register(PartnerProfile)
class PartnerProfileAdmin(admin.ModelAdmin):
    list_display = ("company_name", "user", "tier", "referral_code", "commission_rate", "is_active")
    list_filter = ("tier", "is_active")
    search_fields = ("company_name", "user__email", "referral_code")
    readonly_fields = ("created_at", "updated_at")
