"""Base form classes with design-system widget styling."""

from django import forms


INPUT_CLASS = "form-control"
SELECT_CLASS = "form-control form-control--select"
TEXTAREA_CLASS = "form-control form-control--textarea"
CHECKBOX_CLASS = "form-check-input"
RADIO_CLASS = "form-check-input"


class StyledFormMixin:
    """Apply consistent CSS classes to all form fields."""

    field_css_classes = {
        forms.CharField: INPUT_CLASS,
        forms.EmailField: INPUT_CLASS,
        forms.URLField: INPUT_CLASS,
        forms.IntegerField: INPUT_CLASS,
        forms.DecimalField: INPUT_CLASS,
        forms.FloatField: INPUT_CLASS,
        forms.DateField: INPUT_CLASS,
        forms.DateTimeField: INPUT_CLASS,
        forms.TimeField: INPUT_CLASS,
        forms.UUIDField: INPUT_CLASS,
        forms.RegexField: INPUT_CLASS,
        forms.SlugField: INPUT_CLASS,
        forms.PasswordInput: INPUT_CLASS,
        forms.Textarea: TEXTAREA_CLASS,
        forms.Select: SELECT_CLASS,
        forms.SelectMultiple: SELECT_CLASS,
        forms.CheckboxInput: CHECKBOX_CLASS,
        forms.RadioSelect: RADIO_CLASS,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_field_styles()

    def _apply_field_styles(self):
        for name, field in self.fields.items():
            widget = field.widget
            css_class = self.field_css_classes.get(type(widget), INPUT_CLASS)
            if isinstance(field, (forms.ModelChoiceField, forms.ChoiceField)):
                css_class = SELECT_CLASS
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {css_class}".strip()
            widget.attrs.setdefault("id", f"id_{name}")


class HoneypotMixin:
    """Reject submissions when the hidden honeypot field is filled (bots)."""

    honeypot_field_name = "company_website"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.honeypot_field_name] = forms.CharField(
            required=False,
            widget=forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "tabindex": "-1",
                    "aria-hidden": "true",
                    "class": "hp-field",
                }
            ),
        )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get(self.honeypot_field_name):
            raise forms.ValidationError("Unable to submit your request. Please try again.")
        cleaned.pop(self.honeypot_field_name, None)
        return cleaned


class BaseForm(StyledFormMixin, forms.Form):
    """Reusable styled Form base class."""


class BaseModelForm(StyledFormMixin, forms.ModelForm):
    """Reusable styled ModelForm base class."""
