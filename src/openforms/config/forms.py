from django import forms
from django.utils.translation import gettext_lazy as _

from openforms.forms.models import Form
from openforms.utils.form_fields import (
    CheckboxChoicesArrayField,
    get_arrayfield_choices,
)

from .models import GlobalConfiguration, Theme
from .widgets import DesignTokenValuesTextareaReact, PluginConfigurationTextAreaReact


class UploadFileTypesField(CheckboxChoicesArrayField):
    @staticmethod
    def get_field_choices():
        return get_arrayfield_choices(
            GlobalConfiguration, "form_upload_default_file_types"
        )


class GlobalConfigurationAdminForm(forms.ModelForm):
    class Meta:
        model = GlobalConfiguration
        fields = "__all__"
        field_classes = {
            "form_upload_default_file_types": UploadFileTypesField,
        }
        widgets = {
            "plugin_configuration": PluginConfigurationTextAreaReact,
        }


class ThemeAdminForm(forms.ModelForm):
    class Meta:
        model = Theme
        fields = "__all__"
        widgets = {
            "design_token_values": DesignTokenValuesTextareaReact,
        }

    def clean_design_token_values(self):
        value = self.cleaned_data["design_token_values"]
        return value if value else {}


class ThemePreviewAdminForm(forms.Form):
    form = forms.ModelChoiceField(
        queryset=Form.objects.filter(_is_deleted=False),
        label=_("Form for preview"),
        required=True,
        help_text=_("Pick a form to preview the theme with."),
    )
