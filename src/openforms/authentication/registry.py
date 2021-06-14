from typing import List, Type

from django.http import HttpRequest


class Registry:
    """
    A registry for the authentication module plugins.
    """

    def __init__(self):
        self._registry = {}

    def __call__(self, unique_identifier: str, *args, **kwargs) -> callable:
        def decorator(plugin_cls: Type) -> Type:
            if unique_identifier in self._registry:
                raise ValueError(
                    f"The unique identifier '{unique_identifier}' is already present "
                    "in the registry."
                )
            plugin = plugin_cls(identifier=unique_identifier)
            self._registry[unique_identifier] = plugin
            return plugin_cls

        return decorator

    def __iter__(self):
        return iter(self._registry.values())

    def __getitem__(self, key: str):
        return self._registry[key]

    def get_choices(self):
        return [(p.identifier, p.get_label()) for p in self]

    def get_options(self, request: HttpRequest, form=None) -> List["LoginInfo"]:
        options = list()
        plugins = form.authentication_backends if form else self._registry
        for plugin_id in plugins:
            if plugin_id in self._registry:
                plugin = self._registry[plugin_id]
                info = plugin.get_login_info(request, form)
                options.append(info)
        return options


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
