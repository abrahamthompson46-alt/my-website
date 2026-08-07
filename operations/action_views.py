"""Staff-only POST actions for operations workflows."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from accounts.models import AuditEventType
from accounts.services.audit import log_audit_event
from customer_portal.models.ticket import SupportTicket, TicketStatus
from operations.mixins import StaffRequiredMixin
from payments.models import Payment, PaymentStatus
from payments.services.checkout import confirm_manual_payment
from products.models.demo import DemoRequestStatus, ProductDemoRequest


class DemoRequestUpdateView(StaffRequiredMixin, View):
    def post(self, request, pk):
        demo = get_object_or_404(ProductDemoRequest, pk=pk)
        status = request.POST.get("status", "")
        valid_statuses = {choice[0] for choice in DemoRequestStatus.choices}
        if status not in valid_statuses:
            messages.error(request, "Invalid demo request status.")
            return redirect("operations:demo_requests")

        previous = demo.status
        demo.status = status
        demo.save(update_fields=["status", "updated_at"])
        log_audit_event(
            AuditEventType.DEMO_REQUEST_UPDATED,
            request=request,
            user=request.user,
            message=f"Demo request {demo.pk} status {previous} → {status}",
            metadata={
                "demo_id": str(demo.pk),
                "product_id": str(demo.product_id) if demo.product_id else None,
                "previous_status": previous,
                "new_status": status,
            },
        )
        messages.success(request, f"Demo request updated to {demo.get_status_display()}.")
        return redirect("operations:demo_requests")


class SupportTicketUpdateView(StaffRequiredMixin, View):
    def post(self, request, pk):
        ticket = get_object_or_404(SupportTicket, pk=pk)
        status = request.POST.get("status", "")
        valid_statuses = {choice[0] for choice in TicketStatus.choices}
        if status not in valid_statuses:
            messages.error(request, "Invalid ticket status.")
            return redirect("operations:support")

        ticket.status = status
        ticket.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Ticket {ticket.reference} updated to {ticket.get_status_display()}.")
        return redirect("operations:support")


class ManualPaymentConfirmView(StaffRequiredMixin, View):
    def post(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        if payment.status != PaymentStatus.PENDING_CONFIRMATION:
            messages.error(request, "This payment is not awaiting manual confirmation.")
            return redirect("operations:payments")

        notes = request.POST.get("notes", "").strip()
        try:
            confirm_manual_payment(payment, confirmed_by=request.user, notes=notes)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("operations:payments")

        messages.success(request, f"Payment {payment.reference} confirmed.")
        return redirect("operations:payments")
