from collections import defaultdict
from collections.abc import Callable, Collection, Mapping, Sequence
from datetime import date
from typing import assert_never

from django.utils.translation import gettext as _

from json_logic.typing import Primitive
from rest_framework.exceptions import ErrorDetail

from openforms.formio.service import holds_submission_data
from openforms.formio.typing import Component
from openforms.variables.constants import FormVariableDataTypes

from ...constants import (
    SINGLE_STEP_FORM_ACTION_TYPES,
    FormTypeChoices,
    LogicActionTypes,
)
from ...models import FormVariable
from .typing import FormLogicActionData

type ActionsErrors = defaultdict[int, defaultdict[str, list[ErrorDetail]]]
"""
A mapping of action indices to field errors.

The field errors themselves are a mapping of field name to a collection of errors for
that field. The field names are the keys of a logic action struct (polymorphic).
"""


def validate_logic_actions(
    actions: Sequence[FormLogicActionData],
    *,
    form_type: str,
    find_component: Callable[[str], Component | None],
    form_variables: Mapping[str, FormVariable],
    form_step_slugs: Collection[str],
) -> ActionsErrors:
    """
    Validate a collection of logic rule actions.

    :param actions: The (ordered) collection of actions to verify against the form
      configuration.
    :param form_type: The type of the form.
    :param find_component: An (optimized) callback to resolve a component key against
      a Formio component in any of the form steps.
    :param form_variables: A mapping of all known form variable keys to their form
      variable instance, including both component and user defined variables.
    :param form_step_slugs: A collection of all the form step slugs used in the form.
    """
    errors: ActionsErrors = defaultdict(lambda: defaultdict(list))

    for action_index, action in enumerate(actions):
        # the enum helps enforce the value, and we expect input validation to
        # validate that the action key & type key are present already
        action_type = LogicActionTypes(action["action"]["type"])

        if (
            form_type == FormTypeChoices.single_step
            and action_type not in SINGLE_STEP_FORM_ACTION_TYPES
        ):
            errors[action_index]["type"].append(
                ErrorDetail(
                    _(
                        "Logic action {action_type} is not allowed in single step forms."
                    ).format(action_type=action_type),
                    code="invalid",
                )
            )

        # actions are polymorphic, so their configuration needs to be validated based on
        # the discriminator key. Pattern matching works well for this.

        match action_type:
            # LOGIC_ACTION_TYPES_REQUIRING_COMPONENT
            case LogicActionTypes.property:
                # check that a component is provided
                component_key = action.get("component") or ""
                if not component_key:
                    errors[action_index]["component"].append(
                        ErrorDetail(_("This field may not be blank."), code="blank")
                    )
                    continue

                # now that we know a component is provided, check that it exists
                component = find_component(component_key)
                if component is None:
                    errors[action_index]["component"].append(
                        ErrorDetail(
                            _("Could not find the component with key '{key}'.").format(
                                key=component_key
                            ),
                            code="invalid",
                        )
                    )
                    continue

                # check that "disabled" property is not changed for layout components
                match action["action"]:
                    case {"property": {"value": "disabled"}} if (
                        not holds_submission_data(component)
                    ):
                        errors[action_index]["component"].append(
                            ErrorDetail(
                                _(
                                    "You cannot use the 'disabled' property "
                                    "on layout components'."
                                ),
                                code="invalid",
                            )
                        )
                    case _:
                        pass

            # LOGIC_ACTION_TYPES_REQUIRING_VARIABLE
            case LogicActionTypes.variable:
                # check that a variable is specified
                variable_key = action.get("variable") or ""
                if not variable_key:
                    errors[action_index]["variable"].append(
                        ErrorDetail(_("You must specify a variable."), code="blank")
                    )
                    continue

                # check that the variable exists
                form_var = form_variables.get(variable_key)
                if form_var is None:
                    errors[action_index]["variable"].append(
                        ErrorDetail(
                            _("Could not find the variable with key '{key}'.").format(
                                key=variable_key
                            ),
                            code="invalid",
                        )
                    )
                    continue

                # validate format of value for date variable
                assert "value" in action["action"]
                action_value = action["action"]["value"]
                if (
                    isinstance(action_value, Primitive)
                    and form_var.data_type == FormVariableDataTypes.date
                ):
                    try:
                        # type check muted since we handle it at runtime
                        date.fromisoformat(action_value)  # pyright: ignore[reportArgumentType]
                    except (ValueError, TypeError):
                        errors[action_index]["action.value"].append(
                            ErrorDetail(
                                _(
                                    "The value for a date variable must be a string in "
                                    "the format yyyy-mm-dd (e.g. 2023-07-03)"
                                ),
                                code="invalid",
                            )
                        )

            case (
                LogicActionTypes.step_applicable
                | LogicActionTypes.step_not_applicable
                | LogicActionTypes.disable_next
            ):
                # validate form step slug exists in action
                form_step_slug = action.get("form_step_slug") or ""
                if not form_step_slug:
                    errors[action_index]["formStepSlug"].append(
                        ErrorDetail(_("This field may not be blank."), code="blank")
                    )
                    continue

                # validate form step slug is valid
                if form_step_slug not in form_step_slugs:
                    errors[action_index]["formStepSlug"].append(
                        ErrorDetail(
                            _("Could not find a step with the slug '{slug}'.").format(
                                slug=form_step_slug
                            ),
                            code="invalid",
                        )
                    )
                    continue

            case (
                LogicActionTypes.fetch_from_service
                | LogicActionTypes.set_registration_backend
                | LogicActionTypes.evaluate_dmn
                | LogicActionTypes.synchronize_variables
            ):
                pass
            case _:  # pragma: no cover
                assert_never(action_type)

    return errors
