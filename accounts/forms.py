from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)

from accounts.models import Role, User
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


class InviteUserForm(BaseForm):
    email = forms.EmailField()
    role = forms.ModelChoiceField(queryset=Role.objects.filter(is_active=True).order_by("name"))
    grant_staff_access = forms.BooleanField(
        required=False,
        initial=True,
        label="Grant staff access (Control Room & Operations)",
    )
    message = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Optional welcome note"}),
    )


class UserRoleAssignForm(BaseForm):
    role = forms.ModelChoiceField(queryset=Role.objects.filter(is_active=True).order_by("name"))
    is_staff = forms.BooleanField(required=False, initial=True, label="Staff access")


class AcceptInvitationForm(UserCreationForm):
    first_name = forms.CharField(max_length=120, required=True)
    last_name = forms.CharField(max_length=120, required=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "password1", "password2")

    def __init__(self, *args, invitation_email=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.invitation_email = invitation_email
        if "username" in self.fields:
            del self.fields["username"]
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.invitation_email
        user.username = user.email.split("@")[0][:30]
        base = user.username
        counter = 1
        while User.objects.filter(username=user.username).exclude(pk=user.pk).exists():
            user.username = f"{base}{counter}"[:30]
            counter += 1
        if commit:
            user.save()
        return user


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=120, required=True)
    last_name = forms.CharField(max_length=120, required=True)
    company = forms.CharField(max_length=160, required=False, label="Organization")

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "company", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update(
            {"placeholder": "you@company.com", "autocomplete": "email", "class": "form-control"}
        )
        self.fields["first_name"].widget.attrs.update({"class": "form-control"})
        self.fields["last_name"].widget.attrs.update({"class": "form-control"})
        self.fields["company"].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].widget.attrs.update({"class": "form-control", "autocomplete": "new-password"})
        self.fields["password2"].widget.attrs.update({"class": "form-control", "autocomplete": "new-password"})
        if "username" in self.fields:
            del self.fields["username"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower().strip()
        user.username = user.email.split("@")[0][:30] or "user"
        base = user.username
        counter = 1
        while User.objects.filter(username=user.username).exclude(pk=user.pk).exists():
            user.username = f"{base}{counter}"[:30]
            counter += 1
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user
