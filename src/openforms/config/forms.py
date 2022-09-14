from django import forms

from .models import GlobalConfiguration
from .widgets import PluginConfigurationTextAreaReact


def get_upload_file_types():
    model_field = GlobalConfiguration._meta.get_field("form_upload_default_file_types")
    return model_field.base_field.choices


class UploadFileTypesField(forms.MultipleChoiceField):
    widget = forms.CheckboxSelectMultiple

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("choices", get_upload_file_types)
        for kwarg in ("base_field", "max_length"):
            kwargs.pop(kwarg)
        super().__init__(*args, **kwargs)


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
