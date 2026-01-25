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
    Literal,
    NotRequired,
    Protocol,
    TypedDict,
)

from django.utils.translation import gettext as _

from rest_framework import serializers
from rest_framework.request import Request

from formio_types import TYPE_TO_TAG, AnyComponent, supports_multiple
from formio_types._base import BaseOpenFormsExtensions, SupportedLanguage
from openforms.formio.formatters.formio import DefaultFormatter
from openforms.plugins.plugin import AbstractBasePlugin
from openforms.plugins.registry import BaseRegistry
from openforms.typing import JSONObject, JSONValue, VariableValue
from openforms.variables.constants import FormVariableDataTypes

from .datastructures import FormioConfigurationWrapper, FormioData

if TYPE_CHECKING:
    from openforms.submissions.models import Submission

    from .visibility import GetEvaluationData


class ComponentPreRegistrationResult(TypedDict):
    data: NotRequired[JSONValue]


class FormatterProtocol[ComponentT: AnyComponent](Protocol):
    def __init__(self, as_html: bool): ...

    def __call__(self, component: ComponentT, value: Any) -> str: ...


class NormalizerProtocol[ComponentT: AnyComponent](Protocol):
    def __call__(self, component: ComponentT, value: Any) -> Any: ...


class RewriterForRequestProtocol[ComponentT: AnyComponent](Protocol):
    def __call__(self, component: ComponentT, request: Request) -> None: ...


class PreRegistrationHookProtocol[ComponentT: AnyComponent](Protocol):
    def __call__(
        self, component: ComponentT, submission: Submission
    ) -> ComponentPreRegistrationResult: ...


class BasePlugin[ComponentT: AnyComponent](AbstractBasePlugin, abc.ABC):
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
    ) -> AnyComponent | None: ...

    def localize(
        self, component: ComponentT, language_code: SupportedLanguage, enabled: bool
    ):
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
    def as_json_schema(
        component: ComponentT,
    ) -> JSONObject | list[JSONObject] | None:
        """
        Return JSON schema for this formio component plugin.

        This routine should be implemented in subclasses.
        """
        raise NotImplementedError()

    @staticmethod
    def apply_visibility(
        component: ComponentT,
        data: FormioData,
        wrapper: FormioConfigurationWrapper,
        *,
        data_for_hidden_state: FormioData,
        parent_hidden: bool,
        components_to_ignore_hidden: set[str],
        get_evaluation_data: GetEvaluationData | None = None,
        data_for_visible_state: FormioData | None = None,
    ) -> None:
        """
        Apply (conditional) visibility of this component. This routine should be
        implemented in the child class.

        :param component: Component configuration.
        :param data: Data used for processing.
        :param wrapper: Formio configuration wrapper. Required for component lookup.
        :param data_for_hidden_state: Data to apply when a component is hidden.
        :param parent_hidden: Indicates whether the parent component was hidden.
        :param get_evaluation_data: Function used to get the evaluation data used during
          evaluation of the conditional.
        :param components_to_ignore_hidden: Set of components for which the "hidden"
          property is ignored in determining whether the component is hidden.
        :param data_for_visible_state: The data used to restore values when flipping
          visibility states.
        """
        pass

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
        if getattr(component, "multiple", False):
            return []
        return self.empty_value


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
            component_plugin: BasePlugin[AnyComponent] = self[component_type]
            formatter = component_plugin.formatter(as_html=as_html)
        return formatter(component, value)

    def test_conditional(
        self,
        component: AnyComponent,
        value: VariableValue,
        compare_value: VariableValue,
    ) -> bool:
        """
        Perform a component-specific comparison whether a conditional is triggered.

        :param component: Component to evaluate.
        :param value: Value to evaluate.
        :param compare_value: Value to compare - should be fetched from the conditional
          in the component configuration.
        :return: Whether the conditional was triggered.
        """
        component_type = TYPE_TO_TAG[type(component)]
        if component_type not in self:
            component_type = "default"

        plugin: BasePlugin[AnyComponent] = self[component_type]

        # First, see if the component has a custom test conditional
        if (
            triggered := plugin.test_conditional(component, value, compare_value)
        ) is not None:
            return triggered

        # If it does not have one, default to a membership test if the component is
        # configured as multiple, or a direct comparison otherwise
        if getattr(component, "multiple", False):
            assert isinstance(value, list)
            return compare_value in value
        else:
            return value == compare_value

    def apply_visibility(
        self,
        component: AnyComponent,
        data: FormioData,
        wrapper: FormioConfigurationWrapper,
        *,
        data_for_hidden_state: FormioData,
        parent_hidden: bool,
        components_to_ignore_hidden: set[str],
        get_evaluation_data: Callable | None = None,
        data_for_visible_state: FormioData | None = None,
    ) -> None:
        """
        Apply (conditional) visibility of this component. This routine should be
        implemented in the child class.

        :param component: Component configuration.
        :param data: Data used for processing.
        :param wrapper: Formio configuration wrapper. Required for component lookup.
        :param data_for_hidden_state: Data to apply when a component is hidden.
        :param parent_hidden: Indicates whether the parent component was hidden.
        :param get_evaluation_data: Function used to get the evaluation data used during
          evaluation of the conditional.
        :param components_to_ignore_hidden: Set of components for which the "hidden"
          property is ignored in determining whether the component is hidden.
        :param data_for_visible_state: The data used to restore values when flipping
          visibility states.
        """
        component_type = TYPE_TO_TAG[type(component)]
        plugin: BasePlugin[AnyComponent] = self[component_type]
        plugin.apply_visibility(
            component,
            data,
            wrapper,
            data_for_hidden_state=data_for_hidden_state,
            parent_hidden=parent_hidden,
            get_evaluation_data=get_evaluation_data,
            components_to_ignore_hidden=components_to_ignore_hidden,
            data_for_visible_state=data_for_visible_state,
        )

    def update_config(
        self, component: AnyComponent, submission: Submission, data: FormioData
    ) -> AnyComponent | None:
        """
        Mutate the component configuration in place or return a replacement.

        Mutating the config in place allows dynamic configurations (because of logic,
        for example) to work.
        """
        # if there is no plugin registered for the component, return the input
        component_type = TYPE_TO_TAG[type(component)]
        if component_type not in self:
            return

        # invoke plugin if exists
        plugin: BasePlugin[AnyComponent] = self[component_type]
        return plugin.mutate_config_dynamically(component, submission, data)

    def update_config_for_request(
        self, component: AnyComponent, request: Request
    ) -> None:
        """
        Mutate the component in place for the given request context.
        """
        # if there is no plugin registered for the component, return the input
        component_type = TYPE_TO_TAG[type(component)]
        if component_type not in self:
            return

        # invoke plugin if exists
        rewriter = self[component_type].rewrite_for_request
        if rewriter is None:
            return

        rewriter(component, request)

    def localize_component(
        self, component: AnyComponent, language_code: SupportedLanguage, enabled: bool
    ) -> None:
        """
        Apply component translations for the provided language code.

        :param component: Form.io component definition to localize
        :param language_code: the language code of the language to translate to
        :param enabled: whether translations are enabled or not. If translations are not
          enabled, the translation information should still be stripped from the
          component definition(s).
        """
        of_extensions = getattr(component, "open_forms", None)
        if isinstance(of_extensions, BaseOpenFormsExtensions):
            # apply the generic translation behaviour even for unregistered components
            if (
                enabled
                and (generic_translations := of_extensions.translations) is not None
                and (translations := generic_translations.get(language_code))
                is not None
            ):
                for prop, translation in translations.items():
                    if not translation:
                        continue
                    setattr(component, prop, translation)

            # always drop translation meta information
            if of_extensions.translations:
                of_extensions.translations = None

        # check for component-specific localization hook
        component_type = TYPE_TO_TAG[type(component)]
        if (component_type) in self:
            component_plugin: BasePlugin[AnyComponent] = self[component_type]
            component_plugin.localize(component, language_code, enabled=enabled)

    def build_serializer_field(self, component: AnyComponent) -> serializers.Field:
        """
        Translate a given component into a single serializer field, suitable for
        input validation.
        """
        # if the component known in registry -> use the component plugin, otherwise
        # fall back to the special 'default' plugin which implements the current
        # behaviour of accepting any JSON value.
        component_type = TYPE_TO_TAG[type(component)]
        component_plugin: BasePlugin[AnyComponent] = self[component_type]
        return component_plugin.build_serializer_field(component)

    def as_json_data(
        self, component: AnyComponent, value: VariableValue
    ) -> VariableValue:
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
        component_type = TYPE_TO_TAG[type(component)]
        plugin: BasePlugin[AnyComponent] = self[component_type]
        return plugin.as_json_data(component, value)

    def as_json_schema(
        self, component: AnyComponent
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
        component_type = TYPE_TO_TAG[type(component)]

        plugin: BasePlugin[AnyComponent] = self[component_type]
        schema = plugin.as_json_schema(component)
        if isinstance(schema, dict) and (
            description := getattr(component, "description", "")
        ):
            schema["description"] = description
        return schema

    def has_pre_registration_hook(self, component_type: str) -> bool:
        """
        Determine if a given component has a pre-registration hook.
        """
        if component_type not in self:
            return False
        return self[component_type].pre_registration_hook is not None

    def apply_pre_registration_hook(
        self, component: AnyComponent, submission: Submission
    ) -> ComponentPreRegistrationResult:
        """
        Apply component pre registration hook.
        """
        component_type = TYPE_TO_TAG[type(component)]
        assert self.has_pre_registration_hook(component_type)
        hook = self[component_type].pre_registration_hook

        assert hook is not None

        return hook(component, submission)

    def get_component_data_type(
        self,
        component: AnyComponent,
        ignore_multiple: bool = False,
    ) -> FormVariableDataTypes:
        """
        Determine the data type for the component instance.

        The top-level method takes into account whether the component is scalar or a
        collection of values. The data type is looked up from the component plugin
        registry or defaults to the string type.
        """
        component_type = TYPE_TO_TAG[type(component)]
        plugin: BasePlugin[AnyComponent] = self[component_type]
        if not ignore_multiple and getattr(component, "multiple", False):
            return FormVariableDataTypes.array
        return plugin.get_data_type(component)

    def get_component_data_subtype(
        self, component: AnyComponent
    ) -> Literal[""] | FormVariableDataTypes:
        """
        Get the data subtype of a component.

        :returns: The original data type of the component if the component is configured
          as ``multiple``, an empty string otherwise. Components that are already an
          array (editgrid, files, partners, children and profile) are a special case,
          as ``multiple`` is not relevant for these.
        """
        component_type = TYPE_TO_TAG[type(component)]
        plugin: BasePlugin[AnyComponent] = self[component_type]
        if (subtype := plugin.data_subtype) is not None:
            return subtype

        multiple: bool = component.multiple if supports_multiple(component) else False
        if not multiple:
            return ""

        # get the intrinsic data type
        return self.get_component_data_type(component, ignore_multiple=True)

    def get_empty_value(self, component: AnyComponent) -> JSONValue:
        component_type = TYPE_TO_TAG[type(component)]
        plugin: BasePlugin[AnyComponent] = self[component_type]
        return plugin.get_empty_value(component)

    def holds_submission_data(self, component: AnyComponent) -> bool:
        """Return whether data can be submitted for a particular component."""
        component_type = TYPE_TO_TAG[type(component)]
        if component_type not in self:
            return True
        return self[component_type].holds_submission_data


# Sentinel to provide the default registry. You can easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = ComponentRegistry()
