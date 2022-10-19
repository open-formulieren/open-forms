from django import forms
from django.utils.translation import gettext_lazy as _

from openforms.contrib.kvk.validators import validate_kvk
from openforms.utils.validators import validate_bsn


class RegistratorSubjectInfoForm(forms.Form):
    bsn = forms.CharField(
        label=_("BSN number of client"),
        required=False,
        max_length=9,
        validators=[validate_bsn],
    )
    kvk = forms.CharField(
        label=_("KvK number of client"),
        required=False,
        max_length=8,
        validators=[validate_kvk],
    )
    skip_subject = forms.BooleanField(
        label=_("Continue without additional information"),
        required=False,
        initial=False,
        # TODO make a widget instead of hacking a <button> in the form template
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
