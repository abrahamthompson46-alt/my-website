from common.forms import BaseForm, HoneypotMixin
from django import forms

from products.models import Product


def get_product_choices():
    choices = [("", "Select a product")]
    for product in Product.objects.filter(is_published=True).order_by("sort_order"):
        choices.append((str(product.pk), product.name))
    choices.append(("multiple", "Multiple products"))
    return choices


class DemoRequestForm(HoneypotMixin, BaseForm):
    full_name = forms.CharField(max_length=120, label="Full name")
    work_email = forms.EmailField(label="Work email")
    company = forms.CharField(max_length=200, label="Company")
    phone = forms.CharField(max_length=30, required=False, label="Phone number")
    product_interest = forms.ChoiceField(label="Product of interest", choices=[])
    message = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
        label="Tell us about your needs",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product_interest"].choices = get_product_choices()

    def clean(self):
        cleaned = super().clean()
        from common.services.demo_requests import is_duplicate_demo

        email = cleaned.get("work_email", "")
        product_interest = cleaned.get("product_interest", "")
        product_id = product_interest if product_interest not in ("", "multiple") else None
        if email and is_duplicate_demo(work_email=email, product_id=product_id):
            raise forms.ValidationError(
                "We already received your demo request recently. Our team will contact you soon."
            )
        return cleaned


class NewsletterForm(BaseForm):
    email = forms.EmailField(label="Email address")
