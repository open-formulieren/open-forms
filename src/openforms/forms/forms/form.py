from django import forms
from django.utils.translation import gettext_lazy as _


class FormImportForm(forms.Form):
    file = forms.FileField(
        label=_("file"),
        required=True,
        help_text=_("Upload your exported ZIP-file."),
    )
