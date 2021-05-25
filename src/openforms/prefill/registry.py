from typing import Type


class Registry:
    """
    A registry for the prefill module plugins.
    """

    def __init__(self):
        self._registry = {}

    def __call__(self, unique_identifier: str, *args, **kwargs) -> callable:
        def decorator(plugin_cls: Type) -> Type:

            self._registry[unique_identifier] = plugin_cls

            return plugin_cls

        return decorator

    def __iter__(self):
        return iter(self._registry.values())

    def __getitem__(self, key: str):
        return self._registry[key]


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
