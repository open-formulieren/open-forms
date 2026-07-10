from django import forms
from django.utils.translation import gettext_lazy as _

from openforms.import_export.typing import (
    AdditionalFormConfigurationOptions,
    FormConfigurationOptions,
    LinksToUnknownDomainsOptions,
    ReusableFormDefinitionsOptions,
)


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
    reusable_form_definition = forms.ChoiceField(
        label=_("Reusable form definition"),
        required=False,
        widget=forms.RadioSelect,
        help_text=_(
            "Whether to reuse existing form definitions or create new ones for each "
            "form definition in the import file. "
            "To determine whether a form definition is a duplicate, the title and "
            "configuration are compared. If no comparable form definition exists, a new "
            "form definition is created regardless of the choice."
        ),
        initial=ReusableFormDefinitionsOptions.create_new,
        choices=ReusableFormDefinitionsOptions.choices,
    )
    links_to_unknown_domains = forms.ChoiceField(
        label=_("Links to unknown domains in email templates"),
        required=False,
        widget=forms.RadioSelect,
        help_text=_(
            "What to do with links in email templates to domains that are not accepted "
            "in the global configuration."
        ),
        initial=LinksToUnknownDomainsOptions.ignore,
        choices=LinksToUnknownDomainsOptions.choices,
    )
    additional_form_configuration = forms.MultipleChoiceField(
        label=_("Additional form configuration"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=AdditionalFormConfigurationOptions.choices,
        help_text=_(
            "Which additional form configuration should be included in the export file content."
        ),
    )
