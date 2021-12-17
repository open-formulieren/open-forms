from typing import Any, Dict

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

# from openforms.appointments.registry import register as appointments_register
from openforms.appointments.checks import check_configs as check_appointment_configs
from openforms.config.data import Entry
from openforms.contrib.kvk.checks import check_kvk_remote_validator
from openforms.payments.registry import register as payments_register
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.prefill.registry import register as prefill_register
from openforms.registrations.registry import register as registrations_register
from openforms.utils.mixins import UserIsStaffMixin


def _subset_match(requested: str, checking: str) -> bool:
    if not requested:
        return True
    return requested == checking


class ConfigurationView(UserIsStaffMixin, PermissionRequiredMixin, TemplateView):
    template_name = "admin/config/overview.html"
    permission_required = [
        "accounts.configuration_overview",
    ]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        sections = []

        # undocumented query string support - helps for developers ;)
        module = self.request.GET.get("module")

        # add custom non-generic
        if _subset_match(module, "appointments"):
            sections += [
                {
                    "name": _("Appointment plugins"),
                    "entries": check_appointment_configs(),
                }
            ]

        if _subset_match(module, "address_lookup"):
            sections += [
                {
                    "name": _("Address lookup plugins"),
                    "entries": self.get_address_entries(),
                },
            ]

        if _subset_match(module, "validators"):
            sections += [
                {
                    "name": _("Validator plugins"),
                    "entries": [check_kvk_remote_validator()],
                },
            ]

        # Iterate over all plugin registries.
        plugin_registries = [
            # (_("Appointment plugins"), appointments_register),
            ("registrations", _("Registration plugins"), registrations_register),
            ("prefill", _("Prefill plugins"), prefill_register),
            ("payments", _("Payment plugins"), payments_register),
        ]

        for registry_module, name, register in plugin_registries:
            if not _subset_match(module, registry_module):
                continue
            sections.append(
                {
                    "name": name,
                    "entries": self.get_register_entries(register),
                }
            )

        context.update({"sections": sections})

        return context

    def get_register_entries(self, register):
        for plugin in register.iter_enabled_plugins():
            if hasattr(plugin, "iter_config_checks"):
                yield from plugin.iter_config_checks()
            else:
                yield self.get_plugin_entry(plugin)

    def get_plugin_entry(self, plugin: Any) -> Entry:
        # undocumented query string support - helps for developers ;)
        requested_plugin = self.request.GET.get("plugin")
        if hasattr(plugin, "identifier") and not _subset_match(
            requested_plugin, plugin.identifier
        ):
            return Entry(
                name=plugin.verbose_name,
                status=None,
                status_message=_("Skipped"),
                actions=[],
            )

        try:
            plugin.check_config()
        except InvalidPluginConfiguration as e:
            status_message = e
            status = False
        except NotImplementedError:
            status_message = _("Not implemented")
            status = None
        except Exception as e:
            status_message = _("Internal error: {exception}").format(exception=e)
            status = False
        else:
            status_message = None
            status = True

        try:
            actions = plugin.get_config_actions()
        except NotImplementedError:
            actions = [
                (
                    "Not implemented",
                    "TODO: REMOVE THIS WHEN ALL PLUGINS HAVE THIS FUNCTION.",
                )
            ]
        except Exception as e:
            actions = [
                (
                    _("Internal error: {exception}").format(exception=e),
                    "",
                )
            ]

        return Entry(
            name=plugin.verbose_name,
            status=status,
            status_message=status_message,
            actions=actions,
        )

    def get_address_entries(self):
        try:
            client = import_string(settings.OPENFORMS_LOCATION_CLIENT)
        except ImportError as e:
            return [
                Entry(
                    name=_("unknown"),
                    status=False,
                    status_message=str(e),
                )
            ]
        else:
            return [self.get_plugin_entry(client)]
