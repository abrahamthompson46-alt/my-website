from django import forms

from common.forms import BaseForm, BaseModelForm
from customer_portal.models import CustomerProfile, SupportTicket
from customer_portal.models.ticket import TicketPriority


class ProfileForm(BaseModelForm):
    class Meta:
        model = CustomerProfile
        fields = [
            "company",
            "job_title",
            "phone",
            "timezone",
            "country",
            "email_notifications",
            "product_updates",
            "billing_alerts",
        ]


class UserNameForm(BaseForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)


class SupportTicketForm(BaseModelForm):
    class Meta:
        model = SupportTicket
        fields = ["product", "subject", "description", "priority"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        from products.models import Product

        self.fields["product"].queryset = Product.objects.filter(is_published=True)
        self.fields["product"].required = False
        self.fields["priority"].initial = TicketPriority.NORMAL


class TicketReplyForm(BaseForm):
    body = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Write your reply…"}),
        label="Reply",
    )
