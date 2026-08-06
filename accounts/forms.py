from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)

from common.forms import BaseForm


class MFAChallengeForm(BaseForm):
    code = forms.CharField(
        label="Authentication code",
        max_length=12,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
                "placeholder": "000000",
                "class": "auth-field__input auth-field__input--code",
            }
        ),
    )


class MFAEnrollConfirmForm(BaseForm):
    code = forms.CharField(
        label="Verify authenticator code",
        max_length=12,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
                "placeholder": "000000",
            }
        ),
    )


class MFADisableForm(BaseForm):
    password = forms.CharField(
        label="Current password",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    code = forms.CharField(
        label="Authentication or backup code",
        max_length=12,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "one-time-code", "inputmode": "numeric"}),
    )


class PortalLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email address"
        self.fields["username"].widget.attrs.update(
            {
                "placeholder": "you@company.com",
                "autocomplete": "email",
                "class": "auth-field__input",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "placeholder": "Enter your password",
                "autocomplete": "current-password",
                "class": "auth-field__input",
            }
        )


class PortalPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class EnterprisePasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].label = "Email address"
        self.fields["email"].widget.attrs.update(
            {
                "placeholder": "you@company.com",
                "autocomplete": "email",
                "class": "auth-field__input",
            }
        )


class EnterpriseSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class ResendVerificationForm(BaseForm):
    pass
