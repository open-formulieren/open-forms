"""
Define a single registry for all Formio component types.

Various aspects for formio components are registered in a single place, such as:

* normalization
* formatting of values
* bringing in the render node information

This allows us to treat all aspects of every component type together rather than
smeared out across the codebase in similar but different implementations, while making
the public API better defined and smaller.
"""
from typing import TYPE_CHECKING, Any, Protocol

from openforms.plugins.plugin import AbstractBasePlugin
from openforms.plugins.registry import BaseRegistry
from openforms.typing import DataMapping

from .datastructures import FormioConfigurationWrapper
from .typing import Component

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


class FormatterProtocol(Protocol):
    multiple_separator: str = "; "
    """
    Separator to use for multi-value components.

    Defaults to semi-colon, as formatted numbers already use comma's which hurts
    readability.
    """
    as_html = False
    """
    Format for HTML output or not.

    The default is to format for plain text output, but toggling this will emit
    HTML where relevant.
    """

    # there is an interesting open question on what to do for empty values
    # currently we're eating them in normalise_value_to_list()
    empty_values = [None, ""]

    def __call__(self, component: Component, value: Any, as_html=False) -> str:
        ...

    def format(self, component: Component, value: Any) -> str:
        """
        Format a single value for the given component.
        """
        ...


class BasePlugin(AbstractBasePlugin):
    """
    Base class for Formio component plugins.
    """

    is_enabled: bool = True

    formatter: type[FormatterProtocol]
    """
    Specify the callable to use for formatting.

    Formatter (class) implementation, used by
    :meth:`openforms.formio.registry.ComponentRegistry.format`.
    """

    @staticmethod
    def mutate(component: Component, data: DataMapping) -> None:  # pragma: nocover
        ...


class ComponentRegistry(BaseRegistry):
    module = "formio_components"

    def format(self, info: Component, value: Any, as_html=False):
        """
        Format a given value in the appropriate way for the specified component.

        This results in a human-readable string representation of the value submitted
        for the given component type, as it makes the best sense for that component
        type.
        """
        formatter = (
            register[info["type"]] if info["type"] in register else register["default"]
        )
        return formatter(info, value, as_html=as_html)

    def update_config(
        self, component: Component, data: DataMapping | None = None
    ) -> None:
        """
        Mutate the component configuration in place.

        Mutating the config in place allows dynamic configurations (because of logic,
        for example) to work.
        """
        # if there is no plugin registered for the component, return the input
        if (component_type := component["type"]) not in register:
            return

        # invoke plugin if exists
        plugin = self[component_type]
        plugin.mutate(component, data)

    def handle_custom_types(
        self,
        configuration: FormioConfigurationWrapper,
        submission: "Submission",
    ):
        """
        Process custom backend-only formio types.

        Formio types can be transformed in the context of a given
        :class:`openforms.submissions.models.Submission` and ultimately manifest as
        modified or standard Formio types, essentially performing some sort of "rewrite"
        of the Formio configuration object.
        """
        raise NotImplementedError()


# Sentinel to provide the default registry. You can easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = ComponentRegistry()
