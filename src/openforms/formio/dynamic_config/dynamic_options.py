import json

from django.template.defaultfilters import escape_filter as escape
from django.utils.translation import gettext as _

from glom import assign, glom
from json_logic import jsonLogic

from openforms.logging import logevent
from openforms.submissions.models import Submission
from openforms.typing import DataMapping, JSONValue

from ..typing import Component


def normalise_option(option: JSONValue) -> list[JSONValue]:
    if not isinstance(option, list):
        return [option, option]

    return option[:2]


def is_or_contains_none(option):
    if isinstance(option, list):
        return None in option
    return option is None


def escape_option(option: list[JSONValue]) -> list[str]:
    return [escape(item) for item in option]


def deduplicate_options(
    options: list[JSONValue],
) -> list[JSONValue]:
    new_options = []
    for option in options:
        if option not in new_options:
            new_options.append(option)
    return new_options


def add_options_to_config(
    component: Component,
    data: DataMapping,
    submission: Submission,
    options_path: str = "values",
) -> None:
    if glom(component, "openForms.dataSrc", default=None) != "variable":
        return

    items_expression = glom(component, "openForms.itemsExpression")
    items_array = jsonLogic(items_expression, data)
    if not items_array:
        return

    if not isinstance(items_array, list):
        logevent.form_configuration_error(
            submission.form,
            component,
            _(
                "Variable obtained with expression %(items_expression)s for dynamic options is not an array."
            )
            % {"items_expression": json.dumps(items_expression)},
        )
        return

    # Remove any None values
    if any([is_or_contains_none(item) for item in items_array]):
        logevent.form_configuration_error(
            submission.form,
            component,
            _(
                "Expression %(items_expression)s did not return a valid option for each item."
            )
            % {"items_expression": json.dumps(items_expression)},
        )
        items_array = [item for item in items_array if not is_or_contains_none(item)]

    normalised_options = [normalise_option(option) for option in items_array]
    if any(
        [
            isinstance(item_key, (dict, list)) or isinstance(item_label, (dict, list))
            for item_key, item_label in normalised_options
        ]
    ):
        logevent.form_configuration_error(
            submission.form,
            component,
            _(
                "The dynamic options obtained with expression %(items_expression)s contain non-primitive types."
            )
            % {"items_expression": json.dumps(items_expression)},
        )
        return

    escaped_options = [escape_option(option) for option in normalised_options]
    deduplicated_options = deduplicate_options(escaped_options)
    assign(
        component,
        options_path,
        [
            {"label": escaped_label, "value": escaped_key}
            for escaped_key, escaped_label in deduplicated_options
        ],
        missing=dict,
    )
