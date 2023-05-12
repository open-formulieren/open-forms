from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Submission


class SearchSubmissionForCosignForm(forms.Form):
    code = forms.CharField(
        label=_("Code"),
        help_text=_(
            "You should have received this code in the email requesting you to cosign a form."
        ),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "openforms-input",
            }
        ),
    )
    form_slug = forms.CharField(
        label=_("form slug"),
        help_text=_("The slug of the form to which the submission corresponds."),
        required=True,
        widget=forms.HiddenInput(),
        disabled=True,
    )

    def clean(self):
        if not Submission.objects.filter(
            public_registration_reference=self.cleaned_data["code"],
            form__slug=self.initial["form_slug"],
            cosign_complete=False,
        ).exists():
            raise ValidationError(
                _(
                    "Could not find submission corresponding to this code that requires co-signing"
                )
            )
        return self.cleaned_data
