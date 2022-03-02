from django import forms

from .models import GlobalConfiguration
from .widgets import PluginConfigurationTextAreaReact


class GlobalConfigurationAdminForm(forms.ModelForm):
    class Meta:
        model = GlobalConfiguration
        fields = "__all__"
        widgets = {
            "plugin_configuration": PluginConfigurationTextAreaReact,
        }
