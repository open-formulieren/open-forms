from collections.abc import Callable

from openforms.typing import JSONObject, VariableValue

from .datastructures import FormioConfiguration, FormioConfigurationWrapper, FormioData
from .registry import ComponentRegistry, register
from .typing import Column, Component, ConditionalCompareValue
from .utils import get_component_empty_value


def get_conditional(
    component: Component,
) -> tuple[bool, str, ConditionalCompareValue] | None:
    """
    Get the conditional logic for this component. Will return ``None`` if the
    conditional is not configured or complete.
    """
    conditional = component.get("conditional")
    if not conditional:
        return None

    show = conditional.get("show")
    when = conditional.get("when")
    eq = conditional.get("eq")

    if any([show in ["", None], when in ["", None], eq is None]):
        return None

    return show, when, eq


def test_conditional(
    component: Component,
    value: VariableValue,
    compare_value: VariableValue,
    _register: ComponentRegistry | None = None,
) -> bool:
    """Evaluate a conditional.

    :param component: Component to evaluate.
    :param value: Value to evaluate.
    :param compare_value: Value to compare - should be fetched from the conditional in
      the component configuration.
    :return: Whether the conditional was triggered.
    """
    registry = _register or register

    plugin = registry[component["type"]]

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


def is_hidden_by_conditional(
    component: Component,
    data: FormioData,
    configuration: FormioConfigurationWrapper,
) -> bool:
    """
    Determine whether the component is hidden by the conditional.

    :param component: Component to check.
    :param data: Data context required for the trigger component value.
    :param configuration: Configuration context required for the trigger component
      value.
    :return: Whether the component is hidden.
    """
    conditional = get_conditional(component)

    if conditional is None:
        return False

    show, trigger_component_key, compare_value = conditional

    trigger_component_value = data.get(trigger_component_key, None)
    trigger_component = configuration[trigger_component_key]

    triggered = test_conditional(
        trigger_component, trigger_component_value, compare_value
    )

    # Note that we return whether the component is hidden, not shown, so we invert the
    # return value
    return not show if triggered else show


def process_visibility(
    configuration: FormioConfiguration | Component | Column | JSONObject,
    data: FormioData,
    wrapper: FormioConfigurationWrapper,
    *,
    parent_hidden: bool = False,
    get_evaluation_data: Callable | None = None,
) -> None:
    """
    Process the visibility of the components inside the configuration, by checking if
    they were hidden because of conditional logic or a hidden parent, and clearing the
    value (set to empty component value) when applicable (which is the case unless
    ``clearOnHide`` is ``False``).

    Note that the data mutations are applied directly.

    :param configuration: Configuration-like: can be a Formio configuration, component,
      or column.
    :param data: Data used for processing.
    :param wrapper: Formio configuration wrapper. Required for component lookup.
    :param parent_hidden: Indicates whether the parent component was hidden. Note that
      the conditional will not be evaluated at all when this is set to ``True``.
    :param get_evaluation_data: Function used to get the evaluation data used during
      evaluation of the conditional. If not provided, ``data`` will be used instead.
    """
    for component in configuration.get("components", []):
        key = component["key"]
        clear_on_hide = component.get("clearOnHide", True)

        hidden = parent_hidden or is_hidden_by_conditional(
            component,
            get_evaluation_data(data) if get_evaluation_data else data,
            wrapper,
        )

        # Need to check whether the component is present in the data because layout
        # components have no value
        if hidden and clear_on_hide and key in data:
            data[key] = get_component_empty_value(component)

        # Apply the visibility to children components, if applicable
        apply_visibility(component, data, wrapper, hidden, get_evaluation_data)


def apply_visibility(
    component: Component,
    data: FormioData,
    wrapper: FormioConfigurationWrapper,
    parent_hidden: bool,
    get_evaluation_data: Callable | None = None,
    _register: ComponentRegistry | None = None,
):
    registry = _register or register

    match component["type"]:
        case "softRequiredErrors":
            pass
        case _:
            plugin = registry[component["type"]]
            plugin.apply_visibility(
                component, data, wrapper, parent_hidden, get_evaluation_data
            )
