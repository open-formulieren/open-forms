from typing import Any, Dict

from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

# from openforms.appointments.registry import register as appointments_register
from openforms.payments.registry import register as payments_register
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.prefill.registry import register as prefill_register
from openforms.registrations.registry import register as registrations_register


class ConfigurationView(TemplateView):
    template_name = "admin/config/overview.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        sections = []

        # Iterate over all plugin registries.
        plugin_registries = [
            # (_("Appointment plugins"), appointments_register),
            (_("Registration plugins"), registrations_register),
            (_("Prefill plugins"), prefill_register),
            (_("Payment plugins"), payments_register),
        ]

        for name, register in plugin_registries:
            sections.append(
                {
                    "name": name,
                    "entries": [
                        self.get_plugin_entry(plugin)
                        for plugin in register.iter_enabled_plugins()
                    ],
                }
            )

        context.update({"sections": sections})

        return context

    def get_plugin_entry(self, plugin: Any) -> Dict[str, Any]:
        try:
            plugin.check_config()
        except InvalidPluginConfiguration as e:
            status_message = e
            status = False
        except Exception as e:
            status_message = _("Internal error: {exception}").format(exception=e)
            status = None
        else:
            status_message = None
            status = True

        try:
            actions = plugin.get_config_actions()
        except Exception:
            actions = [
                (
                    "Not implemented",
                    "TODO: REMOVE THIS WHEN ALL PLUGINS HAVE THIS FUNCTION.",
                )
            ]

        return {
            "name": plugin.verbose_name,
            "status": _boolean_icon(status),
            "status_message": status_message,
            "actions": actions,
        }
