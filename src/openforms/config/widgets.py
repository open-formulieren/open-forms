from typing import Any

from django.forms import Textarea

from flags.state import flag_enabled

from openforms.appointments.registry import register as appointments_register
from openforms.authentication.registry import register as auth_register
from openforms.payments.registry import register as payments_register
from openforms.prefill.registry import register as prefill_register
from openforms.registrations.registry import register as registrations_register

PLUGIN_REGISTERS = [
    auth_register,
    payments_register,
    registrations_register,
    prefill_register,
    appointments_register,
]


class PluginConfigurationTextAreaReact(Textarea):
    template_name = "config/forms/plugin_config_react.html"

    class Media:
        css = {
            "all": ("bundles/core-css.css",),
        }
        js = ("bundles/core-js.js",)

    def get_context(self, name: str, value, attrs: dict) -> dict[str, Any]:
        context = super().get_context(name, value, attrs)

        with_demos = flag_enabled("ENABLE_DEMO_PLUGINS")
        modules_and_plugins = {}

        for register in PLUGIN_REGISTERS:
            # AbstractBasePlugin.is_enabled works on self.registry.module and self.identifier
            if not register.module:
                continue
            modules_and_plugins[register.module] = [
                {
                    "identifier": plugin.identifier,
                    "label": plugin.verbose_name,
                }
                for plugin in register
                if not getattr(plugin, "is_demo_plugin", False) or with_demos
            ]

        extra = {"modules_and_plugins": modules_and_plugins}
        return {**context, **extra}


class DesignTokenValuesTextareaReact(Textarea):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("attrs", {})
        clsname = kwargs["attrs"].get("class", "")
        kwargs["attrs"]["class"] = f"{clsname} react-design-token-values".strip()
        super().__init__(*args, **kwargs)

    class Media:
        css = {
            "all": ("bundles/core-css.css",),
        }
        js = ("bundles/core-js.js",)
