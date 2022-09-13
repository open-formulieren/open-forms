from typing import Optional

from openforms.plugins.plugin import AbstractBasePlugin
from openforms.plugins.registry import BaseRegistry
from openforms.typing import DataMapping

from ..typing import Component


class BasePlugin(AbstractBasePlugin):
    is_enabled: bool = True

    @staticmethod
    def mutate(component: Component, data: DataMapping) -> None:  # pragma: nocover
        ...


class Registry(BaseRegistry):
    """
    A registry for the FormIO formatters.
    """

    def update_config(
        self, component: Component, data: Optional[DataMapping] = None
    ) -> None:
        """
        Mutate the component configuration in place.
        """
        # if there is no plugin registered for the component, return the input
        if (component_type := component["type"]) not in register:
            return

        # invoke plugin if exists
        plugin = self[component_type]
        plugin.mutate(component, data)


# Sentinel to provide the default registry. You can easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()
