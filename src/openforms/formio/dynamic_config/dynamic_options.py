import json

from django.template.defaultfilters import escape_filter as escape
from django.utils.translation import gettext as _

from glom import assign, glom
from json_logic import jsonLogic

from openforms.api.exceptions import ServiceUnavailable
from openforms.formio.constants import DataSrcOptions
from openforms.logging import logevent
from openforms.submissions.models import Submission
from openforms.typing import JSONValue

from ..datastructures import FormioData
from ..typing import Component
from .reference_lists import fetch_options_from_reference_lists


def normalise_option(option: JSONValue) -> tuple[JSONValue, JSONValue]:
    if not isinstance(option, list):
        return (option, option)

    return (option[0], option[1])


def is_or_contains_none(option: JSONValue) -> bool:
    if isinstance(option, list):
        return None in option
    return option is None


def escape_option(option: tuple[JSONValue, JSONValue]) -> tuple[str, str]:
    return (escape(str(option[0])), escape(str(option[1])))


def deduplicate_options(
    options: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    new_options = []
    for option in options:
        if option not in new_options:
            new_options.append(option)
    return new_options


def get_options_from_variable(
    component: Component, data: FormioData, submission: Submission
) -> list[tuple[str, str]] | None:
    items_expression = glom(component, "openForms.itemsExpression")
    items_array = jsonLogic(items_expression, data.data)
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
    if len(
        not_none_options := [
            item for item in items_array if not is_or_contains_none(item)
        ]
    ) != len(items_array):
        logevent.form_configuration_error(
            submission.form,
            component,
            _(
                "Expression %(items_expression)s did not return a valid option for each item."
            )
            % {"items_expression": json.dumps(items_expression)},
        )

    normalised_options: list[tuple[JSONValue, JSONValue]] = [
        normalise_option(option) for option in not_none_options
    ]

    if any(
        isinstance(item_key, dict | list) or isinstance(item_label, dict | list)
        for item_key, item_label in normalised_options
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

    return deduplicated_options


def add_options_to_config(
    component: Component,
    data: FormioData,
    submission: Submission,
    options_path: str = "values",
) -> None:
    data_src = glom(component, "openForms.dataSrc", default=None)
    match data_src:
        case DataSrcOptions.reference_lists:
            items_array = fetch_options_from_reference_lists(component, submission)
            if items_array is None:
                raise ServiceUnavailable(
                    _("Could not retrieve options from Referentielijsten API."),
                )
        case DataSrcOptions.variable:
            items_array = get_options_from_variable(component, data, submission)
            if items_array is None:
                return
        case _:
            return

    assign(
        component,
        options_path,
        [
            {"label": escaped_label, "value": escaped_key}
            for escaped_key, escaped_label in items_array
        ],
        missing=dict,
    )
