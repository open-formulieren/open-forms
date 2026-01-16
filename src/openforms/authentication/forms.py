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
        label=_("KvK branche number of customer"),
        help_text=_("Chamber of Commerce branche number of the customer"),
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
        branch_number_msg = _("Branch number is only applicable for KvK values")
        if bsn and kvk:
            self.add_error("bsn", msg)
            self.add_error("kvk", msg)
        elif kvk_branch_number and bsn:
            self.add_error("kvk_branch_number", branch_number_msg)
            self.add_error("bsn", branch_number_msg)
        elif not bsn and not kvk and not skip_subject:
            self.add_error("bsn", msg)
            self.add_error("kvk", msg)
