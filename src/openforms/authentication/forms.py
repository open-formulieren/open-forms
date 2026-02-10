from django import forms
from django.utils.translation import gettext_lazy as _

from openforms.contrib.kvk.validators import validate_branchNumber, validate_kvk
from openforms.utils.validators import validate_bsn
from openforms.utils.widgets import OpenFormsRadioSelect, OpenFormsTextInput

from .constants import ModeChoices


class RegistratorSubjectInfoForm(forms.Form):
    mode = forms.ChoiceField(
        label=_("Continue as..."),
        choices=ModeChoices.choices,
        required=False,
        widget=OpenFormsRadioSelect(
            inline=True,
        ),
    )
    bsn = forms.CharField(
        label=_("BSN of customer"),
        help_text=_("Social security number of the customer"),
        required=False,
        max_length=9,
        validators=[validate_bsn],
        widget=OpenFormsTextInput(
            attrs={
                "pattern": r"\d{9}",
                "placeholder": "_" * 9,
            }
        ),
    )
    kvk = forms.CharField(
        label=_("KvK number of customer"),
        help_text=_("Chamber of Commerce number of the customer"),
        required=False,
        max_length=8,
        validators=[validate_kvk],
        widget=OpenFormsTextInput(),
    )
    kvk_branch_number = forms.CharField(
        label=_("KvK branch number of customer"),
        help_text=_("Chamber of Commerce branch number of the customer"),
        required=False,
        max_length=12,
        validators=[validate_branchNumber],
        widget=OpenFormsTextInput(),
    )
    skip_subject = forms.BooleanField(
        label=_("Continue without additional information"),
        required=False,
        initial=False,
    )

    def clean(self):
        super().clean()

        bsn = self.cleaned_data.get("bsn")
        kvk = self.cleaned_data.get("kvk")
        kvk_branch_number = self.cleaned_data.get("kvk_branch_number")
        skip_subject = self.cleaned_data.get("skip_subject")

        msg = _("Use either BSN or KvK")
        if bsn and kvk:
            self.add_error("bsn", msg)
            self.add_error("kvk", msg)
        elif kvk_branch_number and not kvk:
            self.add_error(
                "kvk_branch_number",
                _("Branch number is only applicable for KvK values"),
            )
        elif not bsn and not kvk and not skip_subject:
            self.add_error("bsn", msg)
            self.add_error("kvk", msg)
