from typing import Type

from openforms.plugins.constants import UNIQUE_ID_MAX_LENGTH


class BaseRegistry:
    """
    Base registry class for plugin modules.
    """

    def __init__(self):
        self._registry = {}

    def __call__(self, unique_identifier: str, *args, **kwargs) -> callable:
        def decorator(plugin_cls: Type) -> Type:
            if len(unique_identifier) > UNIQUE_ID_MAX_LENGTH:
                raise ValueError(
                    f"The unique identifier '{unique_identifier}' is longer then {UNIQUE_ID_MAX_LENGTH} characters."
                )
            if unique_identifier in self._registry:
                raise ValueError(
                    f"The unique identifier '{unique_identifier}' is already present "
                    "in the registry."
                )
            plugin = plugin_cls(identifier=unique_identifier)
            self.check_plugin(plugin)
            self._registry[unique_identifier] = plugin
            return plugin_cls

        return decorator

    def check_plugin(self, plugin):
        # validation hook
        pass

    def __iter__(self):
        return iter(self._registry.values())

    def __getitem__(self, key: str):
        return self._registry[key]

    def __contains__(self, key: str):
        return key in self._registry

    def items(self):
        return iter(self._registry.items())

    def get_choices(self):
        return [(p.identifier, p.get_label()) for p in self]
