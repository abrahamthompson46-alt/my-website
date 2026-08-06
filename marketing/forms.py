from django import forms

from common.forms import BaseForm, BaseModelForm
from marketing.models import NewsletterSubscriber


class NewsletterSubscribeForm(BaseForm):
    email = forms.EmailField(label="Email address")
    full_name = forms.CharField(max_length=120, required=False, label="Full name")

    def save(self, source="website"):
        email = self.cleaned_data["email"].lower()
        subscriber, created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={
                "full_name": self.cleaned_data.get("full_name", ""),
                "source": source,
                "is_active": True,
            },
        )
        if not created and not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save(update_fields=["is_active", "updated_at"])
        return subscriber


class WhitePaperAccessForm(BaseForm):
    email = forms.EmailField(label="Work email")
    full_name = forms.CharField(max_length=120, required=False, label="Full name")

    def save(self, source="whitepaper"):
        form = NewsletterSubscribeForm(data=self.cleaned_data)
        form.is_valid()
        return form.save(source=source)
