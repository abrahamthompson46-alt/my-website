from django.contrib import admin

from ledger.models import Account, BusinessCalendar, BusinessDay, JournalEntry, JournalLine


@admin.register(BusinessCalendar)
class BusinessCalendarAdmin(admin.ModelAdmin):
    list_display = ("organization", "current_business_date", "timezone_name", "updated_at")
    search_fields = ("organization__name", "organization__slug")
    autocomplete_fields = ("organization",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(BusinessDay)
class BusinessDayAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "business_date",
        "status",
        "opened_at",
        "closed_at",
        "trial_balance_debit",
        "trial_balance_credit",
    )
    list_filter = ("status",)
    search_fields = ("organization__name", "organization__slug", "notes")
    autocomplete_fields = ("organization", "closed_by")
    readonly_fields = (
        "organization",
        "business_date",
        "status",
        "opened_at",
        "closed_at",
        "closed_by",
        "notes",
        "trial_balance_debit",
        "trial_balance_credit",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 0
    autocomplete_fields = ("account",)
    readonly_fields = (
        "account",
        "line_no",
        "description",
        "debit_amount",
        "credit_amount",
        "created_at",
        "updated_at",
    )
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "account_type",
        "organization",
        "parent",
        "is_active",
        "currency",
    )
    list_filter = ("account_type", "is_active", "currency")
    search_fields = ("code", "name", "organization__name", "organization__slug")
    autocomplete_fields = ("organization", "parent")
    readonly_fields = ("created_at", "updated_at")


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "organization",
        "business_date",
        "status",
        "currency",
        "posted_at",
        "created_at",
    )
    list_filter = ("status", "currency", "business_date")
    search_fields = ("reference", "description", "organization__name", "organization__slug")
    autocomplete_fields = ("organization", "created_by", "posted_by")
    readonly_fields = (
        "organization",
        "reference",
        "business_date",
        "description",
        "status",
        "currency",
        "posted_at",
        "posted_by",
        "created_by",
        "created_at",
        "updated_at",
    )
    inlines = [JournalLineInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(JournalLine)
class JournalLineAdmin(admin.ModelAdmin):
    list_display = (
        "journal_entry",
        "line_no",
        "account",
        "debit_amount",
        "credit_amount",
    )
    list_filter = ("account__account_type",)
    search_fields = (
        "journal_entry__reference",
        "account__code",
        "account__name",
        "description",
    )
    autocomplete_fields = ("journal_entry", "account")
    readonly_fields = (
        "journal_entry",
        "account",
        "line_no",
        "description",
        "debit_amount",
        "credit_amount",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
