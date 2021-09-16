from typing import List

from django.http import HttpRequest

from openforms.plugins.registry import BaseRegistry

from .base import APIInfo


class Registry(BaseRegistry):
    """
    A registry for the payment module plugins.
    """

    #
    # def check_plugin(self, plugin):
    #     if not plugin.configuration_options:
    #         raise ValueError(
    #             f"Please specify 'configuration_options' attribute for plugin class."
    #         )

    def get_options(self, request: HttpRequest, form=None) -> List["APIInfo"]:
        options = list()
        # TODO clean this up as we support multiple backends on the form
        plugins = [form.payment_backend] if form else self.iter_enabled_plugins()
        for plugin_id in plugins:
            if plugin_id in self._registry:
                plugin = self._registry[plugin_id]
                info = plugin.get_api_info(request, form)
                options.append(info)
        return options


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
