from collections.abc import Generator
from typing import Any, Protocol

from django.utils.encoding import force_str
from django.utils.translation import gettext as _

from typing_extensions import TypeIs

from openforms.appointments.registry import register as appointments_register
from openforms.contrib.brk.checks import BRKValidatorCheck
from openforms.contrib.kadaster.config_check import BAGCheck, LocatieServerCheck
from openforms.contrib.kvk.checks import KVKRemoteValidatorCheck
from openforms.dmn.registry import register as dmn_register
from openforms.payments.registry import register as payments_register
from openforms.plugins.plugin import AbstractBasePlugin
from openforms.prefill.registry import register as prefill_register
from openforms.registrations.registry import register as registrations_register

from .data import Action, Entry


class ConfigCheckable(Protocol):
    verbose_name: str

    @staticmethod
    def check_config() -> None: ...

    @staticmethod
    def get_config_actions() -> list[Action]: ...


def _subset_match(requested: str | None, checking: str) -> bool:
    if not requested:
        return True
    return requested == checking


def is_plugin(plugin: Any) -> TypeIs[AbstractBasePlugin]:
    if hasattr(plugin, "identifier"):
        return True
    return False


class ConfigurationCheck:
    def __init__(self, requested_plugin: str = "") -> None:
        self.requested_plugin = requested_plugin

    def get_configuration_results(
        self, module: str | None = None
    ) -> list[dict[str, Any]]:
        sections = []

        # add custom non-generic
        if _subset_match(module, "address_lookup"):
            sections += [
                {
                    "name": _("Address lookup plugins"),
                    "entries": [
                        self.get_plugin_entry(
                            BAGCheck,
                        ),  # Location client
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

        return sections

    def get_register_entries(self, register) -> Generator[Entry, None, None]:
        for plugin in register.iter_enabled_plugins():
            if hasattr(plugin, "iter_config_checks"):
                yield from plugin.iter_config_checks()
            else:
                yield self.get_plugin_entry(plugin)

    def get_plugin_entry(
        self, plugin: AbstractBasePlugin | type[ConfigCheckable]
    ) -> Entry:
        # undocumented query string support - helps for developers ;)
        status, error = True, ""
        if is_plugin(plugin) and not _subset_match(
            self.requested_plugin, plugin.identifier
        ):
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
            actions: list[Action] = [
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
