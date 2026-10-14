from django import forms
from django.utils.translation import gettext_lazy as _

from openforms.config.models import Theme
from openforms.forms.import_export.constants import (
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
    theme = forms.ModelChoiceField(
        label=_("Theme"),
        required=False,
        help_text=_("Which theme should be used for the imported form."),
        queryset=Theme.objects.all(),
        to_field_name="uuid",
    )
    category = forms.ModelChoiceField(
        label=_("Category"),
        required=False,
        help_text=_("Which category should be applied to the imported form."),
        queryset=Category.objects.all(),
        to_field_name="uuid",
    )
