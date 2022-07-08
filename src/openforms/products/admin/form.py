from django import forms
from django.utils.translation import ugettext_lazy as _


class SchemaImportForm(forms.Form):
    file = forms.FileField(
        label=_("file"),
        required=True,
        help_text=_("Import json file with JSON schema to create a formulier"),
    )
