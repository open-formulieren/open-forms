from typing import Dict, Type

from openforms.registrations.base import BasePlugin


class Registry:
    """
    A registry for registrations module plugins.
    """

    def __init__(self):
        self._registry: Dict[str, BasePlugin] = {}

    def __call__(self, unique_identifier: str, *args, **kwargs) -> callable:
        def decorator(plugin_cls: Type) -> Type:
            if unique_identifier in self._registry:
                raise ValueError(
                    f"The unique identifier '{unique_identifier}' is already present "
                    "in the registry."
                )

            plugin = plugin_cls(unique_identifier)

            if not plugin.configuration_options:
                raise ValueError(
                    f"Please specify 'configuration_options' attribute for plugin class."
                )
            self._registry[unique_identifier] = plugin
            return plugin_cls

        return decorator

    def __iter__(self):
        return iter(self._registry.values())

    def __getitem__(self, key: str):
        return self._registry[key]


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
