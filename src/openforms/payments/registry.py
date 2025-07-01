from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from django.http import HttpRequest

from openforms.plugins.registry import BaseRegistry

from .base import APIInfo, BasePlugin

if TYPE_CHECKING:
    from openforms.forms.models import Form


def _iter_plugin_ids(form: Form | None, registry: Registry) -> Iterator[str]:
    if form is not None:
        # TODO clean this up as we support multiple backends on the form
        yield form.payment_backend
    else:
        for plugin in registry.iter_enabled_plugins():
            yield plugin.identifier


class Registry(BaseRegistry[BasePlugin]):
    """
    A registry for the payment module plugins.
    """

    module = "payments"

    #
    # def check_plugin(self, plugin):
    #     if not plugin.configuration_options:
    #         raise ValueError(
    #             f"Please specify 'configuration_options' attribute for plugin class."
    #         )

    def get_options(
        self, request: HttpRequest, form: Form | None = None
    ) -> list[APIInfo]:
        options = []
        for plugin_id in _iter_plugin_ids(form, self):
            if plugin_id not in self._registry:
                continue
            plugin = self._registry[plugin_id]
            info = plugin.get_api_info(request)
            options.append(info)
        return options


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
