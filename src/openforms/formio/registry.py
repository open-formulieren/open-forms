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

from __future__ import annotations

import abc
from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
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

from openforms.plugins.plugin import AbstractBasePlugin
from openforms.plugins.registry import BaseRegistry
from openforms.typing import JSONObject, JSONValue, VariableValue
from openforms.variables.constants import FormVariableDataTypes

from .typing import Component

if TYPE_CHECKING:
    from openforms.submissions.models import Submission

    from .datastructures import FormioConfigurationWrapper, FormioData

ComponentT = TypeVar("ComponentT", bound=Component, contravariant=True)


class ComponentPreRegistrationResult(TypedDict):
    data: NotRequired[JSONValue]


class FormatterProtocol(Protocol[ComponentT]):
    def __init__(self, as_html: bool): ...

    def __call__(self, component: ComponentT, value: Any) -> str: ...


class NormalizerProtocol(Protocol[ComponentT]):
    def __call__(self, component: ComponentT, value: Any) -> Any: ...


class RewriterForRequestProtocol(Protocol[ComponentT]):
    def __call__(self, component: ComponentT, request: Request) -> None: ...


class PreRegistrationHookProtocol(Protocol[ComponentT]):
    def __call__(
        self, component: ComponentT, submission: Submission
    ) -> ComponentPreRegistrationResult: ...


class BasePlugin(Generic[ComponentT], AbstractBasePlugin, abc.ABC):  # noqa: UP046
    """
    Base class for Formio component plugins.
    """

    formatter: type[FormatterProtocol[ComponentT]]
    """
    Specify the callable to use for formatting.

    Formatter (class) implementation, used by
    :meth:`openforms.formio.registry.ComponentRegistry.format`.
    """
    normalizer: NormalizerProtocol[ComponentT] | None = None
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
    holds_submission_data: ClassVar[bool] = True
    """
    Flag to indicate whether data can be submitted for this component.
    """
    data_type: ClassVar[FormVariableDataTypes] = NotImplemented
    """
    The intrinsic data type for the component, for the non-multiple case.

    Each component type produces values of a certain data type. :attr:`empty_value` is
    expected to be an instance of that data type. Note that components that support the
    ``multiple`` property typically return a list of the intrinsic data type.
    """
    data_subtype: ClassVar[FormVariableDataTypes | None] = None
    """
    The intrinsic item data type for components that have a collection as data type.
    """
    empty_value: ClassVar[JSONValue] = NotImplemented
    """
    The empty value specific to the component type.

    The empty value is used when a component changes visibility state from hidden to
    visible when the value is not or no longer present in the submission data. It's the
    intrinsic starting point for a pristine component state in the UI.

    For empty values that depend on component configuration, override
    :meth:`get_empty_value`.
    """

    @property
    def is_enabled(self) -> Literal[True]:
        return True

    @property
    def verbose_name(self):
        return _("{type} component").format(type=self.identifier.capitalize())

    def mutate_config_dynamically(
        self, component: ComponentT, submission: Submission, data: FormioData
    ) -> None: ...

    def localize(self, component: ComponentT, language_code: str, enabled: bool):
        pass  # noop by default, specific component types can extend the base behaviour

    @abc.abstractmethod
    def build_serializer_field(self, component: ComponentT) -> serializers.Field:
        """Translate a component configuration into a serializer."""

    @staticmethod
    def as_json_data(component: ComponentT, value: VariableValue) -> VariableValue:
        """
        Process the input value for json data output.

        When component-type and/or component-instance specific transformations of the
        raw Formio data are necessary, each component plugin can provide them.

        :param component: The component instance to as context for the variable value.
          Component configuration/options may influence the resulting value.
        :param value: The "raw" component value taken from the Formio data, but already
          converted into the Python domain.
        :returns: The (possibly) processed value to actually use in the JSON output.
        """
        # by default, no processing is necessary and we can just pass-through the
        # value
        return value

    @staticmethod
    def as_json_schema(component: ComponentT) -> JSONObject | list[JSONObject] | None:
        """
        Return JSON schema for this formio component plugin. This routine should be
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
        get_evaluation_data: Callable | None = None,
        data_for_visible_state: FormioData | None = None,
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
        :param data_for_visible_state: The data used to restore values when flipping
          visibility states.
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

    def get_data_type(self, component: ComponentT) -> FormVariableDataTypes:
        return self.data_type

    def get_empty_value(self, component: ComponentT) -> JSONValue:
        if component.get("multiple", False):
            return []
        return self.empty_value


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
        get_evaluation_data: Callable | None = None,
        data_for_visible_state: FormioData | None = None,
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
        :param data_for_visible_state: The data used to restore values when flipping
          visibility states.
        """
        if (component_type := component["type"]) not in self:
            return

        plugin = self[component_type]
        plugin.apply_visibility(
            component,
            data,
            wrapper,
            parent_hidden=parent_hidden,
            get_evaluation_data=get_evaluation_data,
            data_for_visible_state=data_for_visible_state,
        )

    def update_config(
        self, component: Component, submission: Submission, data: FormioData
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

        :param component: Form.io component definition to localize
        :param language_code: the language code of the language to translate to
        :param enabled: whether translations are enabled or not. If translations are not
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

        for index, faq_item in enumerate(component.get("faqItems", [])):
            assert "faqItems" in component
            if "openForms" not in faq_item:
                continue

            faq_translations = faq_item["openForms"]["translations"]
            if language_code not in faq_translations:
                del faq_item["openForms"]["translations"]
                continue

            for property, translation in faq_translations[language_code].items():
                if not translation:
                    break  # don't apply any translation when one is missing
                component["faqItems"][index][property] = translation

            del faq_item["openForms"]["translations"]

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

    def as_json_data(self, component: Component, value: VariableValue) -> VariableValue:
        """
        Process the input value for json data output.

        When component-type and/or component-instance specific transformations of the
        raw Formio data are necessary, each component plugin can provide them.

        :param component: The component instance to as context for the variable value.
          Component configuration/options may influence the resulting value.
        :param value: The "raw" component value taken from the Formio data, but already
          converted into the Python domain.
        :returns: The (possibly) processed value to actually use in the JSON output.

        .. todo:: A generic type at the plugin level to bind the expected value type
           so that ``VariableValue`` is narrowed.
        """
        plugin = self[component["type"]]
        return plugin.as_json_data(component, value)

    def as_json_schema(
        self, component: Component
    ) -> JSONObject | list[JSONObject] | None:
        """
        Return a JSON schema of a component.

        A description will be added if it is available.

        The actual schema building is deferred to each component plugin, which handles
        the nuances for layout components and complex components like editgrids.

        :param component: The component instance to generate a schema for. Component
          configuration/options influence the resulting schema.
        :returns: None for leaf-node components that don't produce a value, a list of
          JSON objects intermediate layout components with child nodes or a single
          JSON object otherwise.
        """
        plugin = self[component["type"]]
        schema = plugin.as_json_schema(component)
        if isinstance(schema, dict) and (description := component.get("description")):
            schema["description"] = description
        return schema

    def has_pre_registration_hook(self, component: Component) -> bool:
        """
        Determine if a given component has a pre-registration hook.
        """
        if (component_type := component["type"]) not in self:
            return False

        return self[component_type].pre_registration_hook is not None

    def apply_pre_registration_hook(
        self, component: Component, submission: Submission
    ) -> ComponentPreRegistrationResult:
        """
        Apply component pre registration hook.
        """
        assert self.has_pre_registration_hook(component)
        hook = self[component["type"]].pre_registration_hook

        assert hook is not None

        return hook(component, submission)

    def get_component_data_type(self, component: Component) -> FormVariableDataTypes:
        """
        Determine the data type for the component instance.

        The top-level method takes into account whether the component is scalar or a
        collection of values. The data type is looked up from the component plugin
        registry or defaults to the string type.
        """
        if component.get("multiple"):
            return FormVariableDataTypes.array
        if (component_type := component["type"]) not in self:
            return FormVariableDataTypes.string
        return self[component_type].get_data_type(component)

    def get_component_data_subtype(
        self, component: Component
    ) -> Literal[""] | FormVariableDataTypes:
        """
        Get the data subtype of a component.

        :returns: The original data type of the component if the component is configured
          as ``multiple``, an empty string otherwise. Components that are already an
          array (editgrid, files, partners, children and profile) are a special case,
          as ``multiple`` is not relevant for these.
        """
        if (component_type := component["type"]) not in self:
            component_type = "default"

        if (subtype := self[component_type].data_subtype) is not None:
            return subtype

        if not component.get("multiple"):
            return ""

        # get the intrinsic data type
        _component: Component = {**component, "multiple": False}
        return self.get_component_data_type(_component)

    def get_empty_value(self, component: Component) -> JSONValue:
        if (component_type := component["type"]) not in self:
            return ""
        return self[component_type].get_empty_value(component)

    def holds_submission_data(self, component: Component) -> bool:
        """Return whether data can be submitted for a particular component."""
        if (component_type := component["type"]) not in self:
            return True

        return self[component_type].holds_submission_data


# Sentinel to provide the default registry. You can easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = ComponentRegistry()
