from typing import TYPE_CHECKING, List

from django.http import HttpRequest

from openforms.plugins.registry import BaseRegistry

if TYPE_CHECKING:
    from .base import LoginInfo


class Registry(BaseRegistry):
    """
    A registry for the authentication module plugins.
    """

    def get_options(self, request: HttpRequest, form=None) -> List["LoginInfo"]:
        options = list()
        plugins = form.authentication_backends if form else self.iter_enabled_plugins()
        for plugin_id in plugins:
            if plugin_id in self._registry:
                plugin = self._registry[plugin_id]
                info = plugin.get_login_info(request, form)
                options.append(info)
        return options

    def get_choices(self):
        return [(p.identifier, p.get_label()) for p in self if p.is_enabled]


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
