from django.contrib import admin, messages
from django.utils import timezone

from payments.models import (
    GatewayConfiguration,
    ManualPaymentDetail,
    Payment,
    PaymentAttempt,
    ReconciliationEntry,
    ReconciliationRun,
    RecurringPayment,
    Refund,
    WebhookEvent,
)
from payments.services.checkout import confirm_manual_payment
from payments.services.reconciliation import run_reconciliation


@admin.register(GatewayConfiguration)
class GatewayConfigurationAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "is_default", "supports_recurring", "supports_refunds")
    list_filter = ("is_active", "code", "supports_recurring")
    search_fields = ("name", "code")


class PaymentAttemptInline(admin.TabularInline):
    model = PaymentAttempt
    extra = 0
    readonly_fields = ("status", "gateway_reference", "error_message", "created_at")


class ManualPaymentDetailInline(admin.StackedInline):
    model = ManualPaymentDetail
    extra = 0


class RefundInline(admin.TabularInline):
    model = Refund
    extra = 0
    readonly_fields = ("reference", "amount", "status", "gateway_refund_id", "created_at")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "gateway", "amount", "currency", "status", "manual_method", "paid_at")
    list_filter = ("status", "gateway", "payment_type", "manual_method", "currency")
    search_fields = ("reference", "gateway_reference", "user__email", "customer_email")
    readonly_fields = ("reference", "gateway_reference", "idempotency_key", "paid_at", "failed_at")
    inlines = [ManualPaymentDetailInline, PaymentAttemptInline, RefundInline]
    actions = ["confirm_manual_payments"]

    @admin.action(description="Confirm selected manual payments")
    def confirm_manual_payments(self, request, queryset):
        confirmed = 0
        for payment in queryset.filter(status="pending_confirmation"):
            try:
                confirm_manual_payment(payment, request.user)
                confirmed += 1
            except ValueError:
                continue
        self.message_user(request, f"Confirmed {confirmed} manual payment(s).", messages.SUCCESS)


@admin.register(RecurringPayment)
class RecurringPaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "gateway", "amount", "currency", "interval", "status", "next_charge_at")
    list_filter = ("status", "gateway", "interval")
    search_fields = ("reference", "gateway_subscription_id", "user__email")


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("reference", "payment", "amount", "currency", "status", "initiated_by", "processed_at")
    list_filter = ("status", "currency")
    search_fields = ("reference", "gateway_refund_id", "payment__reference")


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("gateway", "event_type", "event_id", "signature_valid", "processed", "created_at")
    list_filter = ("gateway", "processed", "signature_valid")
    search_fields = ("event_id", "event_type")
    readonly_fields = ("payload", "headers", "created_at")


class ReconciliationEntryInline(admin.TabularInline):
    model = ReconciliationEntry
    extra = 0
    readonly_fields = ("payment", "gateway_reference", "internal_reference", "is_matched", "discrepancy")


@admin.register(ReconciliationRun)
class ReconciliationRunAdmin(admin.ModelAdmin):
    list_display = (
        "gateway",
        "period_start",
        "period_end",
        "status",
        "gateway_total",
        "internal_total",
        "discrepancy_amount",
        "matched_count",
        "unmatched_count",
    )
    list_filter = ("status", "gateway")
    inlines = [ReconciliationEntryInline]
    actions = ["run_reconciliation_for_period"]

    @admin.action(description="Re-run reconciliation (internal records only)")
    def run_reconciliation_for_period(self, request, queryset):
        for run in queryset:
            run_reconciliation(
                run.gateway,
                run.period_start,
                run.period_end,
                run_by=request.user,
            )
        self.message_user(request, "Reconciliation re-run completed.", messages.SUCCESS)
