from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol

from formio_types import (
    AnyComponent,
    Columns,
    CosignV1,
    SoftRequiredErrors,
)
from formio_types._base import Conditional
from openforms.typing import VariableValue

from .registry import register
from .typing import Component

if TYPE_CHECKING:
    from .datastructures import FormioConfig, FormioConfigurationWrapper, FormioData


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
    component: AnyComponent,
    data: FormioData,
    configuration: FormioConfig,
) -> bool:
    """
    Determine whether the component is hidden by checking the conditional and "hidden"
    property (optional).

    :param component: Component to check.
    :param data: Data context required for the trigger component value.
    :param configuration: Configuration context required for the trigger component
      value.
    :return: Whether the component is hidden.
    """
    conditional = get_conditional(component)

    if conditional is None:
        match component:
            case SoftRequiredErrors():
                return False
            case _:
                return component.hidden

    # the assertion cases must be filtered out by ``get_conditional`` and result in
    # "there is no conditional specified"
    assert conditional.when is not None
    assert isinstance(conditional.show, bool)

    show = conditional.show
    trigger_component_key = conditional.when
    compare_value = conditional.eq

    # Be resilient on the component key lookup
    # XXX: configuration validation must enforce that triggers point to valid
    # components
    if trigger_component_key in configuration:
        trigger_component = configuration[trigger_component_key]

        # Defaulting to an empty string when the value is nullish is what our renderer
        # does, with a note that it may need some revision later because it's a
        # left-over formio relic.
        trigger_component_value: VariableValue = (
            v if (v := data.get(trigger_component_key, None)) is not None else ""
        )
        triggered = register.test_conditional(
            trigger_component,
            trigger_component_value,
            compare_value,
        )
    else:
        # when the 'when' reference is broken, we don't have a component to interpret
        # the compare value. In that case, default to the empty string, which is what
        # formio does when it has no value for a component.
        triggered = compare_value == ""

    # Note that we return whether the component is hidden, not shown, so we invert the
    # return value
    return not show if triggered else show


def process_visibility(
    components: Sequence[AnyComponent] | Sequence[Component],
    data: FormioData,
    wrapper: FormioConfigurationWrapper,
    *,
    parent_hidden: bool = False,
    get_evaluation_data: GetEvaluationData | None = None,
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
    :param parent_hidden: Indicates whether the parent component was hidden. Note that
      the conditional will not be evaluated at all when this is set to ``True``.
    :param get_evaluation_data: Function used to get the evaluation data used during
      evaluation of the conditional. If not provided, ``data`` will be used instead.
    :param data_for_visible_state: The data used to restore values when flipping
      visibility states.
    """
    from .datastructures import FormioConfig
    from .service import _convert_legacy_component

    # process legacy structures into their msgspec equivalents, as this is the top-level
    # entry point for a number of call sites working with legacy typed dicts
    # TODO: update call sites to convert to msgspec earlier, which requires cleaning up
    # the whole submissions logic evalution :)))
    components = [
        _convert_legacy_component(comp) if isinstance(comp, dict) else comp
        for comp in components
    ]

    for component in components:
        key = component.key
        # FIXME: only consider components that define clear_on_hide (e.g. exclude content)
        clear_on_hide = getattr(component, "clear_on_hide", True)

        hidden = parent_hidden or is_hidden(
            component,
            get_evaluation_data(data) if get_evaluation_data else data,
            # XXX convert FormioConfigurationWrapper to FormioConfig, but be careful that
            # downstream call mutations will not be reflected upstream!
            FormioConfig(
                name="<converted from FormioConfigurationWrapper>",
                components=wrapper.configuration["components"],
            ),
        )

        # Need to check whether the component holds submission data, as we do not have
        # to clear those that don't (fieldset, content, softRequiredErrors, etc.)
        holds_submission_data = register.holds_submission_data(component)
        if hidden and clear_on_hide and holds_submission_data:
            data.pop(key, None)

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
            parent_hidden=hidden,
            get_evaluation_data=get_evaluation_data,
            data_for_visible_state=data_for_visible_state,
        )
