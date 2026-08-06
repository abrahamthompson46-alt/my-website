from common.forms import BaseForm
from django import forms

from products.models import Product


def get_product_choices():
    choices = [("", "Select a product")]
    for product in Product.objects.filter(is_published=True).order_by("sort_order"):
        choices.append((str(product.pk), product.name))
    choices.append(("multiple", "Multiple products"))
    return choices


class DemoRequestForm(BaseForm):
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


class NewsletterForm(BaseForm):
    email = forms.EmailField(label="Email address")
