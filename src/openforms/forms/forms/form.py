from django import forms
from django.utils.translation import ugettext_lazy as _


class FormImportForm(forms.Form):
    file = forms.FileField(
        label=_("file"),
        required=True,
        help_text=_(
            "The ZIP-file that contains either a single exported form or multiple ZIP-files of exported forms."
        ),
    )
