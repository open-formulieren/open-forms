from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from openforms.utils.widgets import OpenFormsTextInput

from .models import Submission


class SearchSubmissionForCosignForm(forms.Form):
    code = forms.CharField(
        label=_("Code"),
        help_text=_(
            "You should have received this code in the email requesting you to cosign a form."
        ),
        required=True,
        widget=OpenFormsTextInput(),
    )

    def __init__(self, instance, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.form = instance

    def clean(self):
        submission = Submission.objects.filter(
            public_registration_reference=self.cleaned_data["code"],
            form=self.form,
            cosign_complete=False,
        ).first()
        if not submission:
            raise ValidationError(
                _(
                    "Could not find a submission corresponding to this code that requires co-signing"
                )
            )
        self.cleaned_data["submission"] = submission
        return self.cleaned_data
