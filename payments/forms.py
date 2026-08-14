from django import forms

from common.forms import BaseForm
from payments.models import ManualPaymentMethod
from payments.validators import validate_proof_file_extension, validate_proof_file_size


class CheckoutForm(BaseForm):
    gateway = forms.CharField(widget=forms.HiddenInput(), required=False)
    description = forms.CharField(max_length=255, required=False)
    manual_method = forms.ChoiceField(
        choices=[("", "Online payment")] + list(ManualPaymentMethod.choices),
        required=False,
    )
    bank_name = forms.CharField(max_length=120, required=False)
    transfer_reference = forms.CharField(max_length=128, required=False)
    cheque_number = forms.CharField(max_length=64, required=False)
    receipt_number = forms.CharField(max_length=64, required=False)
    notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)
    proof_document = forms.FileField(
        required=False,
        validators=[validate_proof_file_extension, validate_proof_file_size],
        help_text="Upload a PDF or image (PNG, JPG, WEBP) up to 5 MB.",
    )

    def clean(self):
        cleaned = super().clean()
        manual_method = cleaned.get("manual_method")
        if not manual_method:
            return cleaned

        if manual_method == ManualPaymentMethod.BANK_TRANSFER:
            if not cleaned.get("bank_name", "").strip():
                self.add_error("bank_name", "Bank name is required for bank transfers.")
            if not cleaned.get("transfer_reference", "").strip():
                self.add_error("transfer_reference", "Transfer reference is required for bank transfers.")
        elif manual_method == ManualPaymentMethod.CHEQUE:
            if not cleaned.get("cheque_number", "").strip():
                self.add_error("cheque_number", "Cheque number is required.")
        elif manual_method == ManualPaymentMethod.CASH:
            if not cleaned.get("receipt_number", "").strip():
                self.add_error("receipt_number", "Receipt number is required.")

        if not cleaned.get("proof_document"):
            self.add_error("proof_document", "Upload proof of payment for manual methods.")

        return cleaned


class RefundForm(BaseForm):
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    reason = forms.CharField(max_length=255, required=False)
