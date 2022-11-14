from django import forms
from django.utils.translation import gettext_lazy as _

from openforms.contrib.kvk.validators import validate_kvk
from openforms.utils.validators import validate_bsn
from openforms.utils.widgets import OpenFormsRadioSelect

from .constants import ModeChoices


class RegistratorSubjectInfoForm(forms.Form):
    mode = forms.ChoiceField(
        label=_("Continue as..."),
        choices=ModeChoices.choices,
        required=False,
        widget=OpenFormsRadioSelect,
    )
    bsn = forms.CharField(
        label=_("BSN number of client"),
        required=False,
        max_length=9,
        validators=[validate_bsn],
        widget=forms.TextInput(
            attrs={
                "class": "openforms-input",
                "pattern": r"\d{9}",
                "placeholder": "_" * 9,
            }
        ),
    )
    kvk = forms.CharField(
        label=_("KvK number of client"),
        required=False,
        max_length=8,
        validators=[validate_kvk],
        widget=forms.TextInput(attrs={"class": "openforms-input"}),
    )
    skip_subject = forms.BooleanField(
        label=_("Continue without additional information"),
        required=False,
        initial=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        bsn = cleaned_data.get("bsn")
        kvk = cleaned_data.get("kvk")
        skip_subject = cleaned_data.get("skip_subject")

        msg = _("Use either BSN or KvK")
        if bsn and kvk:
            self.add_error("bsn", msg)
            self.add_error("kvk", msg)
        elif not bsn and not kvk and not skip_subject:
            self.add_error("bsn", msg)
            self.add_error("kvk", msg)
