from django import forms
from django.utils.translation import gettext_lazy as _

from openforms.config.models import Theme
from openforms.forms.import_export.typing import (
    AdditionalFormConfigurationOptions,
    FormConfigurationOptions,
)
from openforms.forms.models import Category


class FormImportForm(forms.Form):
    file = forms.FileField(
        label=_("file"),
        required=True,
        help_text=_("Upload your exported ZIP-file."),
    )
    form_configuration = forms.MultipleChoiceField(
        label=_("Form configuration"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        initial=[
            FormConfigurationOptions.registration_backends,
            FormConfigurationOptions.prefill,
            FormConfigurationOptions.payment_backend,
            FormConfigurationOptions.auth_backends,
        ],
        choices=FormConfigurationOptions.choices,
        help_text=_(
            "Which form configuration should be included in the export file content."
        ),
    )
    additional_form_configuration = forms.MultipleChoiceField(
        label=_("Additional form configuration"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=AdditionalFormConfigurationOptions.choices,
        help_text=_(
            "Which additional form configuration should be included in the export file "
            "content."
        ),
    )
    reuse_form_definitions = forms.BooleanField(
        label=_("Re-use form definitions"),
        required=False,
        initial=True,
        help_text=_(
            "Whether to re-use existing form definitions or create new form definitions "
            "for each form definition in the import file. (If no matching reusable form "
            "definition is found, a new one will be created.)"
        ),
    )
    theme = forms.ModelChoiceField(
        label=_("Theme"),
        required=False,
        help_text=_("Which theme should be used for the imported form."),
        queryset=Theme.objects.all(),
    )
    category = forms.ModelChoiceField(
        label=_("Category"),
        required=False,
        help_text=_("Which category should be applied to the imported form."),
        queryset=Category.objects.all(),
    )
