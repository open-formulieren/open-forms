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

import warnings
from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Literal,
    NotRequired,
    Protocol,
    TypedDict,
    TypeVar,
)

from django.utils.translation import gettext as _

from rest_framework import serializers
from rest_framework.request import Request

from formio_types import TYPE_TO_TAG, AnyComponent
from openforms.formio.formatters.formio import DefaultFormatter
from openforms.plugins.plugin import AbstractBasePlugin
from openforms.plugins.registry import BaseRegistry
from openforms.typing import JSONObject, JSONValue, VariableValue

from .datastructures import FormioConfigurationWrapper, FormioData
from .typing import Component
from .utils import is_layout_component

if TYPE_CHECKING:
    from openforms.submissions.models import Submission

ComponentT = TypeVar("ComponentT", bound=Component, contravariant=True)
NewComponentT = TypeVar("NewComponentT", bound=AnyComponent)


class ComponentPreRegistrationResult(TypedDict):
    data: NotRequired[JSONValue]


class FormatterProtocol[ComponentT: AnyComponent](Protocol):
    def __init__(self, as_html: bool): ...

    def __call__(self, component: ComponentT, value: Any) -> str: ...


class NormalizerProtocol[ComponentT: AnyComponent](Protocol):
    def __call__(self, component: ComponentT, value: Any) -> Any: ...


class RewriterForRequestProtocol(Protocol[ComponentT]):
    def __call__(self, component: ComponentT, request: Request) -> None: ...


class PreRegistrationHookProtocol(Protocol[ComponentT]):
    def __call__(
        self, component: ComponentT, submission: "Submission"
    ) -> ComponentPreRegistrationResult: ...


class BasePlugin(Generic[ComponentT, NewComponentT], AbstractBasePlugin):
    """
    Base class for Formio component plugins.
    """

    formatter: type[FormatterProtocol[NewComponentT]]
    """
    Specify the callable to use for formatting.

    Formatter (class) implementation, used by
    :meth:`openforms.formio.registry.ComponentRegistry.format`.
    """
    normalizer: NormalizerProtocol[NewComponentT] | None = None
    """
    Specify the normalizer callable to use for value normalization.
    """
    rewrite_for_request: RewriterForRequestProtocol[ComponentT] | None = None
    """
    Callback to invoke to rewrite plugin configuration for a given HTTP request.
    """
    pre_registration_hook: PreRegistrationHookProtocol[ComponentT] | None = None
    """
    Hook to perform component-specific registration logic during the "pre-registration" phase.
    """

    @property
    def is_enabled(self) -> Literal[True]:
        return True

    @property
    def verbose_name(self):
        return _("{type} component").format(type=self.identifier.capitalize())

    def mutate_config_dynamically(
        self, component: ComponentT, submission: "Submission", data: FormioData
    ) -> None: ...

    def localize(self, component: ComponentT, language_code: str, enabled: bool):
        pass  # noop by default, specific component types can extend the base behaviour

    def build_serializer_field(self, component: ComponentT) -> serializers.Field:
        # the default implementation is a compatibility shim while we transition to
        # the new backend validation mechanism.
        warnings.warn(
            "Relying on the default/implicit JSONField for component type "
            f"{component['type']} is deprecated. Instead, define the "
            "'build_serializer_field' method on the specific component plugin.",
            DeprecationWarning,
            stacklevel=2,
        )

        # not considered a layout component (because it doesn't have children)
        if component["type"] == "content":
            required = False
        elif is_layout_component(component):
            required = False  # they do not hold data, they can never be required
        else:
            required = (
                validate.get("required", False)
                if (validate := component.get("validate"))
                else False
            )

        # Allow anything that is valid JSON, taking into account the 'required'
        # validation which is common for most components.
        return serializers.JSONField(required=required, allow_null=True)

    @staticmethod
    def as_json_schema(component: NewComponentT) -> JSONObject:
        """Return JSON schema for this formio component plugin. This routine should be
        implemented in the child class
        """
        raise NotImplementedError()

    @staticmethod
    def apply_visibility(
        component: ComponentT,
        data: FormioData,
        wrapper: FormioConfigurationWrapper,
        *,
        parent_hidden: bool,
        ignore_hidden_property: bool,
        get_evaluation_data: Callable | None = None,
    ) -> None:
        """
        Apply (conditional) visibility of this component. This routine should be
        implemented in the child class.

        :param component: Component configuration.
        :param data: Data used for processing.
        :param wrapper: Formio configuration wrapper. Required for component lookup.
        :param parent_hidden: Indicates whether the parent component was hidden.
        :param get_evaluation_data: Function used to get the evaluation data used during
          evaluation of the conditional.
        :param ignore_hidden_property: Whether to ignore the "hidden" property during
          further processing of its children.
        """

    @staticmethod
    def test_conditional(
        component: ComponentT, value: VariableValue, compare_value: VariableValue
    ) -> bool | None:
        """
        Perform a component-specific comparison whether a conditional is triggered.

        :param component: Component to evaluate.
        :param value: Value to evaluate.
        :param compare_value: Value to compare - should be fetched from the conditional
          in the component configuration.
        :return: Whether the conditional was triggered, or ``None`` if not overridden in
          the child class.
        """
        return None


class ComponentRegistry(BaseRegistry[BasePlugin]):
    module = "formio_components"

    def normalize(self, component: AnyComponent, value: Any) -> Any:
        """
        Given a value from any source, normalize it according to the component rules.
        """
        component_type = TYPE_TO_TAG[type(component)]
        if component_type not in self:
            return value
        normalizer = self[component_type].normalizer
        if normalizer is None:
            return value
        return normalizer(component, value)

    def format(self, component: AnyComponent, value: Any, as_html=False) -> str:
        """
        Format a given value in the appropriate way for the specified component.

        This results in a human-readable string representation of the value submitted
        for the given component type, as it makes the best sense for that component
        type.
        """
        component_type = TYPE_TO_TAG[type(component)]
        if component_type not in self:
            formatter = DefaultFormatter(as_html=as_html)
        else:
            component_plugin = self[component_type]
            formatter = component_plugin.formatter(as_html=as_html)
        return formatter(component, value)

    def test_conditional(
        self, component: Component, value: VariableValue, compare_value: VariableValue
    ) -> bool:
        """
        Perform a component-specific comparison whether a conditional is triggered.

        :param component: Component to evaluate.
        :param value: Value to evaluate.
        :param compare_value: Value to compare - should be fetched from the conditional
          in the component configuration.
        :return: Whether the conditional was triggered.
        """
        if (component_type := component["type"]) not in self:
            component_type = "default"

        plugin = self[component_type]

        # First, see if the component has a custom test conditional
        if (
            triggered := plugin.test_conditional(component, value, compare_value)
        ) is not None:
            return triggered

        # If it does not have one, default to a membership test if the component is
        # configured as multiple, or a direct comparison otherwise
        if component.get("multiple", False):
            assert isinstance(value, list)
            return compare_value in value
        else:
            return value == compare_value

    def apply_visibility(
        self,
        component: Component,
        data: FormioData,
        wrapper: FormioConfigurationWrapper,
        *,
        parent_hidden: bool,
        ignore_hidden_property: bool,
        get_evaluation_data: Callable | None = None,
    ) -> None:
        """
        Apply (conditional) visibility of this component. This routine should be
        implemented in the child class.

        :param component: Component configuration.
        :param data: Data used for processing.
        :param wrapper: Formio configuration wrapper. Required for component lookup.
        :param parent_hidden: Indicates whether the parent component was hidden.
        :param get_evaluation_data: Function used to get the evaluation data used during
          evaluation of the conditional.
        :param ignore_hidden_property: Whether to ignore the "hidden" property during
          further processing of its children.
        """
        if (component_type := component["type"]) not in self:
            return

        plugin = self[component_type]
        plugin.apply_visibility(
            component,
            data,
            wrapper,
            parent_hidden=parent_hidden,
            ignore_hidden_property=ignore_hidden_property,
            get_evaluation_data=get_evaluation_data,
        )

    def update_config(
        self, component: Component, submission: "Submission", data: FormioData
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

    def localize_component(
        self, component: Component, language_code: str, enabled: bool
    ) -> None:
        """
        Apply component translations for the provided language code.

        :arg component: Form.io component definition to localize
        :arg language_code: the language code of the language to translate to
        :arg enabled: whether translations are enabled or not. If translations are not
          enabled, the translation information should still be stripped from the
          component definition(s).
        """
        generic_translations = component.get("openForms", {}).get("translations", {})
        # apply the generic translation behaviour even for unregistered components
        if enabled and (translations := generic_translations.get(language_code, {})):
            for prop, translation in translations.items():
                if not translation:
                    continue
                component[prop] = translation

        if (component_type := component["type"]) in self:
            component_plugin = self[component_type]
            component_plugin.localize(component, language_code, enabled=enabled)

        # always drop translation meta information
        if generic_translations:
            del component["openForms"]["translations"]  # type: ignore

    def build_serializer_field(self, component: Component) -> serializers.Field:
        """
        Translate a given component into a single serializer field, suitable for
        input validation.
        """
        # if the component known in registry -> use the component plugin, otherwise
        # fall back to the special 'default' plugin which implements the current
        # behaviour of accepting any JSON value.
        if (component_type := component["type"]) not in self:
            component_type = "default"

        component_plugin = self[component_type]
        return component_plugin.build_serializer_field(component)

    def has_pre_registration_hook(self, component: Component) -> bool:
        """
        Determine if a given component has a pre-registration hook.
        """
        if (component_type := component["type"]) not in self:
            return False

        return self[component_type].pre_registration_hook is not None

    def apply_pre_registration_hook(
        self, component: Component, submission: "Submission"
    ) -> ComponentPreRegistrationResult:
        """
        Apply component pre registration hook.
        """
        assert self.has_pre_registration_hook(component)
        hook = self[component["type"]].pre_registration_hook

        assert hook is not None

        return hook(component, submission)


# Sentinel to provide the default registry. You can easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = ComponentRegistry()
