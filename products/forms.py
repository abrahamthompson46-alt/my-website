from common.forms import BaseForm, BaseModelForm, HoneypotMixin
from django import forms
from django.core.exceptions import ValidationError

from common.services.demo_requests import is_duplicate_demo
from products.models import Product, ProductDemoRequest


class ProductDemoRequestForm(HoneypotMixin, BaseModelForm):
    class Meta:
        model = ProductDemoRequest
        fields = ["full_name", "work_email", "company", "phone", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("work_email", "")
        product_id = self.product.pk if self.product else None
        if email and is_duplicate_demo(work_email=email, product_id=product_id):
            raise ValidationError(
                "We already received your demo request recently. Our team will contact you soon."
            )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.product = self.product
        if commit:
            instance.save()
        return instance


class ProductCompareSelectForm(BaseForm):
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.filter(is_published=True),
        widget=forms.CheckboxSelectMultiple,
        label="Select products to compare",
        required=True,
    )

    def clean_products(self):
        products = self.cleaned_data["products"]
        if len(products) < 2:
            raise forms.ValidationError("Select at least two products to compare.")
        if len(products) > 4:
            raise forms.ValidationError("You can compare up to four products at a time.")
        return products
