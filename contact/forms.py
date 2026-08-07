from django import forms

from website.forms import DemoRequestForm


INTENT_CHOICES = [
    ("demo", "Request a demo"),
    ("trial", "Start a free trial"),
]


class ContactLeadForm(DemoRequestForm):
    intent = forms.ChoiceField(
        label="I'm interested in",
        choices=INTENT_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "intent-radio"}),
    )

    def __init__(self, *args, initial_intent="demo", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["intent"].initial = initial_intent if initial_intent in dict(INTENT_CHOICES) else "demo"
