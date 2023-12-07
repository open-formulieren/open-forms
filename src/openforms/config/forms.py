from django import forms

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
