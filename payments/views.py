import json
import logging

from django.contrib import messages
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, ListView, TemplateView

from core.media_paths import is_private_media_path
from customer_portal.mixins import PortalMixin
from payments.constants import MANUAL
from payments.forms import CheckoutForm
from payments.gateways.registry import list_available_gateways
from payments.models import GatewayConfiguration, ManualPaymentDetail, ManualPaymentMethod, Payment, PaymentStatus
from payments.services.checkout import create_checkout
from payments.services.pricing import CheckoutPricingError, resolve_checkout_pricing
from payments.services.webhooks import process_webhook, verify_payment
from products.models import PricingPlan, PricingTier

logger = logging.getLogger("payments")


class PaymentListView(PortalMixin, ListView):
    model = Payment
    template_name = "payments/payment_list.html"
    context_object_name = "payments"
    paginate_by = 20

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).select_related("gateway").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Payments"},
        ]
        return context


class PaymentDetailView(PortalMixin, DetailView):
    model = Payment
    template_name = "payments/payment_detail.html"
    context_object_name = "payment"

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).select_related("gateway", "invoice")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Payments", "url_name": "payments:list"},
            {"label": self.object.reference},
        ]
        manual_detail = getattr(self.object, "manual_detail", None)
        if manual_detail and manual_detail.proof_document:
            context["payment_proof_url"] = reverse(
                "payments:proof_download",
                kwargs={"pk": self.object.pk},
            )
        return context


def _resolve_plan_checkout(request):
    plan_id = request.GET.get("plan") or request.POST.get("plan_id")
    tier_id = request.GET.get("tier") or request.POST.get("tier_id")
    if not plan_id:
        return None, None
    plan = get_object_or_404(
        PricingPlan.objects.select_related("product"),
        pk=plan_id,
        is_published=True,
        is_contact_sales=False,
    )
    tier = None
    if tier_id:
        tier = get_object_or_404(PricingTier, pk=tier_id, plan=plan)
    else:
        tier = plan.tiers.first()
    if not tier or tier.amount is None:
        raise ValueError("Selected plan has no purchasable price.")
    return plan, tier


class CheckoutView(PortalMixin, TemplateView):
    template_name = "payments/checkout.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form", CheckoutForm())
        context["gateways"] = list_available_gateways()
        context["manual_methods"] = ManualPaymentMethod
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Payments", "url_name": "payments:list"},
            {"label": "Checkout"},
        ]
        invoice_id = self.request.GET.get("invoice")
        if invoice_id:
            from customer_portal.models import Invoice

            context["invoice"] = get_object_or_404(
                Invoice, pk=invoice_id, user=self.request.user
            )
        try:
            plan, tier = _resolve_plan_checkout(self.request)
        except ValueError as exc:
            messages.error(self.request, str(exc))
            plan = tier = None
        if plan and tier:
            context["pricing_plan"] = plan
            context["pricing_tier"] = tier
        return context

    def post(self, request, *args, **kwargs):
        form = CheckoutForm(request.POST, request.FILES)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        gateway_code = form.cleaned_data.get("gateway") or None
        manual_method = form.cleaned_data.get("manual_method")
        if manual_method:
            gateway_code = MANUAL

        try:
            pricing = resolve_checkout_pricing(
                user=request.user,
                invoice_id=request.POST.get("invoice_id"),
                plan_id=request.POST.get("plan_id"),
                tier_id=request.POST.get("tier_id"),
                posted_amount=request.POST.get("amount"),
                posted_currency=request.POST.get("currency"),
            )
        except CheckoutPricingError as exc:
            messages.error(request, str(exc))
            return self.render_to_response(self.get_context_data(form=form))

        amount = pricing["amount"]
        currency = pricing["currency"]
        invoice = pricing["invoice"]
        pricing_plan = pricing["pricing_plan"]
        pricing_tier = pricing["pricing_tier"]

        manual_detail = {}
        if manual_method == "bank_transfer":
            manual_detail = {
                "bank_name": form.cleaned_data.get("bank_name", ""),
                "transfer_reference": form.cleaned_data.get("transfer_reference", ""),
                "notes": form.cleaned_data.get("notes", ""),
            }
        elif manual_method == "cheque":
            manual_detail = {
                "cheque_number": form.cleaned_data.get("cheque_number", ""),
                "notes": form.cleaned_data.get("notes", ""),
            }
        elif manual_method == "cash":
            manual_detail = {
                "receipt_number": form.cleaned_data.get("receipt_number", ""),
                "notes": form.cleaned_data.get("notes", ""),
            }
        proof = form.cleaned_data.get("proof_document")
        if manual_method and proof:
            manual_detail["proof_document"] = proof

        description = form.cleaned_data.get("description", "")
        if pricing_plan and not description:
            description = f"{pricing_plan.product.name} — {pricing_plan.name}"

        try:
            payment, result = create_checkout(
                user=request.user,
                amount=amount,
                currency=currency,
                gateway_code=gateway_code,
                description=description,
                customer_email=request.user.email,
                callback_url=request.build_absolute_uri(
                    reverse("payments:return", kwargs={"reference": "TEMPREF"})
                ),
                invoice=invoice,
                pricing_plan=pricing_plan,
                pricing_tier=pricing_tier,
                manual_method=manual_method or "",
                manual_detail=manual_detail or None,
            )
            payment.callback_url = request.build_absolute_uri(
                reverse("payments:return", kwargs={"reference": payment.reference})
            )
            payment.save(update_fields=["callback_url", "updated_at"])
        except (ValueError, CheckoutPricingError) as exc:
            messages.error(request, str(exc))
            return self.render_to_response(self.get_context_data(form=form))

        if payment.authorization_url:
            return redirect(payment.authorization_url)
        messages.success(request, result.message or "Payment initiated.")
        return redirect("payments:detail", pk=payment.pk)


class PaymentReturnView(PortalMixin, View):
    def get(self, request, reference):
        payment = get_object_or_404(Payment, reference=reference, user=request.user)
        if payment.status not in {PaymentStatus.SUCCEEDED, PaymentStatus.REFUNDED}:
            verify_payment(payment)
            payment.refresh_from_db()
        if payment.status == PaymentStatus.SUCCEEDED:
            messages.success(request, "Payment completed successfully.")
            try:
                from common.services.onboarding_email import send_payment_receipt_email

                send_payment_receipt_email(request.user, payment)
            except Exception:
                logger.exception("Failed to send payment receipt email")
        elif payment.status == PaymentStatus.PENDING_CONFIRMATION:
            messages.info(request, "Your payment is awaiting confirmation.")
        else:
            messages.warning(request, "Payment verification pending or failed.")
        return redirect("payments:detail", pk=payment.pk)


class PaymentProofDownloadView(PortalMixin, View):
    """Serve payment proof documents only to the owner or staff."""

    def get(self, request, pk):
        payment = get_object_or_404(Payment.objects.select_related("manual_detail"), pk=pk)
        if payment.user_id != request.user.id and not request.user.is_staff:
            raise Http404("Payment proof not found.")

        detail = getattr(payment, "manual_detail", None)
        if not detail or not detail.proof_document:
            raise Http404("Payment proof not found.")

        file_field = detail.proof_document
        if not file_field.name or not is_private_media_path(file_field.name):
            logger.warning("Blocked payment proof download for non-private path: %s", file_field.name)
            raise Http404("Payment proof not found.")

        filename = file_field.name.rsplit("/", 1)[-1]
        return FileResponse(file_field.open("rb"), as_attachment=False, filename=filename)


@method_decorator(csrf_exempt, name="dispatch")
class GatewayWebhookView(View):
    """Provider-agnostic webhook endpoint: /payments/webhooks/<gateway_code>/"""

    def post(self, request, gateway_code):
        gateway_config = get_object_or_404(GatewayConfiguration, code=gateway_code, is_active=True)
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return HttpResponse(status=400)

        headers = {k: v for k, v in request.headers.items()}
        try:
            webhook_event, _ = process_webhook(gateway_config, payload, request.body, headers)
        except Exception:
            logger.exception("Webhook processing failed for %s", gateway_code)
            return JsonResponse({"status": "error", "message": "Webhook processing failed."}, status=500)

        if webhook_event.error_message and not webhook_event.processed:
            return JsonResponse({"status": "rejected", "message": webhook_event.error_message}, status=400)
        return JsonResponse({"status": "ok"})
