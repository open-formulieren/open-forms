from typing import Any, Generator, Optional, Protocol, TypeGuard

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from openforms.appointments.registry import register as appointments_register
from openforms.contrib.brk.checks import BRKValidatorCheck
from openforms.contrib.kadaster.config_check import BAGCheck, LocatieServerCheck
from openforms.contrib.kvk.checks import KVKRemoteValidatorCheck
from openforms.dmn.registry import register as dmn_register
from openforms.payments.registry import register as payments_register
from openforms.plugins.plugin import AbstractBasePlugin
from openforms.prefill.registry import register as prefill_register
from openforms.registrations.registry import register as registrations_register
from openforms.utils.mixins import UserIsStaffMixin

from .data import Action, Entry
from .models import GlobalConfiguration
from .utils import verify_clamav_connection


def _subset_match(requested: Optional[str], checking: str) -> bool:
    if not requested:
        return True
    return requested == checking


class ConfigCheckable(Protocol):
    verbose_name: str

    def check_config(self) -> None:
        ...

    def get_config_actions(self) -> list[Action]:
        ...


def is_plugin(plugin: Any) -> TypeGuard[AbstractBasePlugin]:
    if hasattr(plugin, "identifier"):
        return True
    return False


class ConfigurationView(UserIsStaffMixin, PermissionRequiredMixin, TemplateView):
    template_name = "admin/config/overview.html"
    permission_required = [
        "accounts.configuration_overview",
    ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        sections = []

        # undocumented query string support - helps for developers ;)
        module = self.request.GET.get("module")

        # add custom non-generic
        if _subset_match(module, "address_lookup"):
            sections += [
                {
                    "name": _("Address lookup plugins"),
                    "entries": [
                        self.get_plugin_entry(BAGCheck),  # Location client
                        self.get_plugin_entry(LocatieServerCheck),  # Kadaster search
                    ],
                },
            ]

        if _subset_match(module, "validators"):
            sections += [
                {
                    "name": _("Validator plugins"),
                    "entries": [
                        # uses KVK 'zoeken' client
                        self.get_plugin_entry(KVKRemoteValidatorCheck),
                        self.get_plugin_entry(BRKValidatorCheck),
                    ],
                },
            ]

        # Iterate over all plugin registries.
        plugin_registries = [
            ("appointments", _("Appointment plugins"), appointments_register),
            ("registrations", _("Registration plugins"), registrations_register),
            ("prefill", _("Prefill plugins"), prefill_register),
            ("payments", _("Payment plugins"), payments_register),
            ("dmn", _("DMN plugins"), dmn_register),
        ]

        for registry_module, name, register in plugin_registries:
            if not _subset_match(module, registry_module):
                continue
            sections.append(
                {
                    "name": name,
                    "entries": list(self.get_register_entries(register)),
                }
            )

        sections.append({"name": "Anti-virus", "entries": [self.get_clamav_entry()]})

        context.update({"sections": sections})

        return context

    def get_register_entries(self, register) -> Generator[Entry, None, None]:
        for plugin in register.iter_enabled_plugins():
            if hasattr(plugin, "iter_config_checks"):
                yield from plugin.iter_config_checks()
            else:
                yield self.get_plugin_entry(plugin)

    def get_plugin_entry(self, plugin: AbstractBasePlugin | ConfigCheckable) -> Entry:
        # undocumented query string support - helps for developers ;)
        requested_plugin = self.request.GET.get("plugin")
        status, error = True, ""
        if is_plugin(plugin) and not _subset_match(requested_plugin, plugin.identifier):
            return Entry(
                name=force_str(plugin.verbose_name),
                status=None,
                actions=[],
            )

        try:
            plugin.check_config()
        except Exception as e:
            status, error = False, str(e)

        try:
            actions = plugin.get_config_actions()
        except Exception as e:
            actions = [
                (
                    _("Internal error: {exception}").format(exception=e),
                    "",
                )
            ]

        return Entry(
            name=force_str(plugin.verbose_name),
            status=status,
            actions=actions,
            error=error,
        )

    def get_clamav_entry(self):
        config = GlobalConfiguration.get_solo()
        assert isinstance(config, GlobalConfiguration)
        config_url = reverse(
            "admin:config_globalconfiguration_change", args=(config.pk,)
        )
        if not config.enable_virus_scan:
            return Entry(
                name="ClamAV",
                status=None,
                actions=[
                    (_("Configuration"), config_url),
                ],
            )

        result = verify_clamav_connection(
            host=config.clamav_host,
            port=config.clamav_port,
            timeout=config.clamav_timeout,
        )

        return Entry(
            name="ClamAV",
            status=result.can_connect,
            error=result.error,
            actions=[
                (
                    _("Configuration"),
                    config_url,
                ),
            ],
        )
