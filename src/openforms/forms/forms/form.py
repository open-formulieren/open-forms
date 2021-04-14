from django import forms
from django.utils.translation import ugettext_lazy as _


class FormImportForm(forms.Form):
    file = forms.FileField(
        label=_("bestand"),
        required=True,
        help_text=_("Het ZIP-bestand met het formulier."),
    )
