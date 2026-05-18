from typing import Protocol

from formio_types import AnyComponent, Columns, CosignV1, SoftRequiredErrors
from formio_types._base import Conditional
from openforms.typing import JSONObject, JSONValue

from .datastructures import FormioConfiguration, FormioConfigurationWrapper, FormioData
from .registry import register
from .typing import Column, Component
from .utils import get_component_empty_value as _get_component_empty_value


class GetEvaluationData(Protocol):
    def __call__(self, data: FormioData) -> FormioData:
        """Get evaluation data context."""
        ...


def get_conditional(component: AnyComponent) -> Conditional | None:
    """
    Get the conditional logic for this component. Will return ``None`` if the
    conditional is not configured or complete.
    """
    match component:
        # these don't support conditionals at all
        case Columns() | SoftRequiredErrors() | CosignV1():
            return None
        case _:
            conditional: Conditional | None = component.conditional

    if conditional is None:
        return None

    # test that the conditional is properly configured
    show = conditional.show
    when = conditional.when
    eq = conditional.eq
    if any([show in ["", None], when in ["", None], eq is None]):
        return None

    return conditional


def is_hidden(
    component: Component,
    data: FormioData,
    configuration: FormioConfigurationWrapper,
    ignore_hidden_property: bool,
) -> bool:
    """
    Determine whether the component is hidden by checking the conditional and "hidden"
    property (optional).

    :param component: Component to check.
    :param data: Data context required for the trigger component value.
    :param configuration: Configuration context required for the trigger component
      value.
    :param ignore_hidden_property: Whether to ignore the "hidden" property in
      determining if the component is hidden. Note that this is only relevant if there
      is no (valid) conditional present. If there is a conditional, it will take
      precedence.
    :return: Whether the component is hidden.
    """
    from .service import _convert_legacy_component

    _component = _convert_legacy_component(component)
    conditional = get_conditional(_component)

    if conditional is None:
        if ignore_hidden_property:
            return False
        match _component:
            case SoftRequiredErrors():
                return False
            case _:
                return _component.hidden

    assert conditional.when is not None
    assert isinstance(conditional.show, bool)

    show = conditional.show
    trigger_component_key = conditional.when
    compare_value = conditional.eq

    trigger_component_value = data.get(trigger_component_key, None)
    trigger_component = _convert_legacy_component(configuration[trigger_component_key])

    triggered = register.test_conditional(
        trigger_component,
        trigger_component_value,
        compare_value,
    )

    # Note that we return whether the component is hidden, not shown, so we invert the
    # return value
    return not show if triggered else show


def get_component_empty_value(component: Component) -> JSONValue:
    if component["type"] in ("date", "time", "datetime"):
        return None
    return _get_component_empty_value(component)


def process_visibility(
    configuration: FormioConfiguration | Component | Column | JSONObject,
    data: FormioData,
    wrapper: FormioConfigurationWrapper,
    *,
    data_for_hidden_state: FormioData,
    parent_hidden: bool = False,
    get_evaluation_data: GetEvaluationData | None = None,
    components_to_ignore_hidden: set[str] | None = None,
    data_for_visible_state: FormioData | None = None,
) -> None:
    """
    Process the visibility of the components inside the configuration, by checking if
    they were hidden because of conditional logic or a hidden parent, and clearing the
    value when applicable (``clearOnHide`` is ``True``).

    Note that the data mutations are applied directly.

    :param configuration: Configuration-like: can be a Formio configuration, component,
      or column.
    :param data: Data used for processing.
    :param wrapper: Formio configuration wrapper. Required for component lookup.
    :param data_for_hidden_state: Data to apply when a component is hidden.
    :param parent_hidden: Indicates whether the parent component was hidden. Note that
      the conditional will not be evaluated at all when this is set to ``True``.
    :param get_evaluation_data: Function used to get the evaluation data used during
      evaluation of the conditional. If not provided, ``data`` will be used instead.
    :param components_to_ignore_hidden: Set of components for which the "hidden"
      property is ignored in determining whether the component is hidden. Note that if
      it was not passed, the hidden property WILL be checked.
    :param data_for_visible_state: The data used to restore values when flipping
      visibility states.
    """
    components_to_ignore_hidden = components_to_ignore_hidden or set()
    for component in configuration.get("components", []):
        key = component["key"]
        clear_on_hide = component.get("clearOnHide", True)

        hidden = parent_hidden or is_hidden(
            component,
            get_evaluation_data(data) if get_evaluation_data else data,
            wrapper,
            key in components_to_ignore_hidden,
        )

        # Need to check whether the component holds submission data, as we do not have
        # to clear those that don't (fieldset, content, softRequiredErrors, etc.)
        holds_submission_data = register.holds_submission_data(component)
        if hidden and clear_on_hide and holds_submission_data:
            # NOTE - formio.js (and our own renderer) *delete* the key entirely from the
            # data instead, while we assign the empty value to ensure every variable is
            # always present in the submission data
            # If we don't have an initial value available, just use the empty value.
            data[key] = data_for_hidden_state.get(key) or get_component_empty_value(
                component
            )

        # if it's visible, check if any input data should be restored because earlier
        # logic rules may have cleared it (visible -> hidden -> visible)
        if not hidden and data_for_visible_state is not None and holds_submission_data:
            if data.get(key) != (original_value := data_for_visible_state.get(key)):
                # restore the value from the original input data - likely there was a
                # sequence in logic that lead to the data being cleared because of hidden
                # state, while a subsequent action makes the component visible again. In
                # that case, the frontend will have the component visible and data can
                # be entered, which needs to be grabbed from the initial data to avoid
                # wiping user input.
                data[key] = original_value

        # Apply the visibility to children components, if applicable
        register.apply_visibility(
            component,
            data,
            wrapper,
            data_for_hidden_state=data_for_hidden_state,
            parent_hidden=hidden,
            get_evaluation_data=get_evaluation_data,
            components_to_ignore_hidden=components_to_ignore_hidden,
            data_for_visible_state=data_for_visible_state,
        )
