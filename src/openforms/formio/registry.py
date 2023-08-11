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

from django.utils.translation import gettext as _

from rest_framework.request import Request

from openforms.plugins.plugin import AbstractBasePlugin
from openforms.plugins.registry import BaseRegistry
from openforms.typing import DataMapping

from .typing import Component

if TYPE_CHECKING:  # pragma: nocover
    from openforms.submissions.models import Submission


class FormatterProtocol(Protocol):  # pragma: nocover
    def __init__(self, as_html: bool):
        ...

    def __call__(self, component: Component, value: Any) -> str:
        ...


class NormalizerProtocol(Protocol):  # pragma: nocover
    def __call__(self, component: Component, value: Any) -> Any:
        ...


class RewriterForRequestProtocol(Protocol):  # pragma: nocover
    def __call__(self, component: Component, request: Request) -> None:
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
    normalizer: None | NormalizerProtocol = None
    """
    Specify the normalizer callable to use for value normalization.
    """
    rewrite_for_request: None | RewriterForRequestProtocol = None
    """
    Callback to invoke to rewrite plugin configuration for a given HTTP request.
    """

    @property
    def verbose_name(self):
        return _("{type} component").format(type=self.identifier.capitalize())

    def mutate_config_dynamically(
        self, component: Component, submission: "Submission", data: DataMapping
    ) -> None:  # pragma: nocover
        ...


class ComponentRegistry(BaseRegistry[BasePlugin]):
    module = "formio_components"

    def normalize(self, component: Component, value: Any) -> Any:
        """
        Given a value from any source, normalize it according to the component rules.
        """
        if (component_type := component["type"]) not in self:
            return value
        normalizer = self[component_type].normalizer
        if normalizer is None:
            return value
        return normalizer(component, value)

    def format(self, component: Component, value: Any, as_html=False) -> str:
        """
        Format a given value in the appropriate way for the specified component.

        This results in a human-readable string representation of the value submitted
        for the given component type, as it makes the best sense for that component
        type.
        """
        if (component_type := component["type"]) not in self:
            component_type = "default"

        component_plugin = self[component_type]
        formatter = component_plugin.formatter(as_html=as_html)
        return formatter(component, value)

    def update_config(
        self,
        component: Component,
        submission: "Submission",
        data: DataMapping | None = None,
    ) -> None:
        """
        Mutate the component configuration in place.

        Mutating the config in place allows dynamic configurations (because of logic,
        for example) to work.
        """
        # if there is no plugin registered for the component, return the input
        if (component_type := component["type"]) not in self:
            return

        # invoke plugin if exists
        plugin = self[component_type]
        plugin.mutate_config_dynamically(component, submission, data)

    def update_config_for_request(self, component: Component, request: Request) -> None:
        """
        Mutate the component in place for the given request context.
        """
        # if there is no plugin registered for the component, return the input
        if (component_type := component["type"]) not in self:
            return

        # invoke plugin if exists
        rewriter = self[component_type].rewrite_for_request
        if rewriter is None:
            return

        rewriter(component, request)


# Sentinel to provide the default registry. You can easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = ComponentRegistry()
