from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING

from django.db import OperationalError

from flags.state import flag_enabled

from .constants import UNIQUE_ID_MAX_LENGTH

if TYPE_CHECKING:
    from .plugin import AbstractBasePlugin


class BaseRegistry[PluginT: AbstractBasePlugin]:
    """
    Base registry class for plugin modules.
    """

    module: str = ""
    """
    The name of the 'module' this registry belongs to.

    The module is the logical group of extra functionality in Open Forms on top of the
    core functionality.
    """
    _registry: dict[str, PluginT]

    def __init__(self):
        self._registry = {}

    def __call__(
        self, unique_identifier: str
    ) -> Callable[[type[PluginT]], type[PluginT]]:
        if len(unique_identifier) > UNIQUE_ID_MAX_LENGTH:
            raise ValueError(
                f"The unique identifier '{unique_identifier}' is longer than "
                f"{UNIQUE_ID_MAX_LENGTH} characters."
            )

        def decorator(plugin_cls: type[PluginT]) -> type[PluginT]:
            if unique_identifier in self._registry:
                raise ValueError(
                    f"The unique identifier '{unique_identifier}' is already present "
                    "in the registry."
                )

            plugin = plugin_cls(identifier=unique_identifier)
            self.check_plugin(plugin)
            plugin.registry = self
            self._registry[unique_identifier] = plugin
            return plugin_cls

        return decorator

    def check_plugin(self, plugin: PluginT):
        # validation hook
        pass

    def __iter__(self):
        return iter(self._registry.values())

    def __getitem__(self, key: str) -> PluginT:
        return self._registry[key]

    def __contains__(self, key: str) -> bool:
        return key in self._registry

    def iter_enabled_plugins(self) -> Iterator[PluginT]:
        try:
            with_demos = flag_enabled("ENABLE_DEMO_PLUGINS")
            enable_all = False
        except OperationalError:
            # fix CI trying to access non-existing database to generate OAS
            with_demos = False
            enable_all = True

        for plugin in self:
            is_demo = getattr(plugin, "is_demo_plugin", False)
            if is_demo and not with_demos:
                continue
            elif enable_all or plugin.is_enabled:  # plugins are enabled by default
                yield plugin

    def items(self):
        return iter(self._registry.items())

    def get_choices(self):
        return [(p.identifier, p.get_label()) for p in self.iter_enabled_plugins()]
