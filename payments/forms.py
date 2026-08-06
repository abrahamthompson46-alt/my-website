from django import forms

from common.forms import BaseForm
from payments.constants import MANUAL
from payments.models import ManualPaymentMethod


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


class RefundForm(BaseForm):
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    reason = forms.CharField(max_length=255, required=False)
