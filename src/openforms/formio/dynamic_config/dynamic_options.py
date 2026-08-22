import json
from typing import assert_never

from django.template.defaultfilters import escape_filter as escape
from django.utils.translation import gettext as _

from json_logic import jsonLogic

from formio_types import Option, Radio, Select, Selectboxes
from openforms.api.exceptions import ServiceUnavailable
from openforms.formio.constants import DataSrcOptions
from openforms.formio.service import dump_to_legacy
from openforms.logging import audit_logger
from openforms.submissions.models import Submission
from openforms.typing import JSONValue

from ..datastructures import FormioData
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
    # convert to regular string instead of SafeString
    return (escape(str(option[0]))[:], escape(str(option[1]))[:])


def deduplicate_options(
    options: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    new_options = []
    for option in options:
        if option not in new_options:
            new_options.append(option)
    return new_options


def get_options_from_variable(
    component: Radio | Select | Selectboxes, data: FormioData, submission: Submission
) -> list[tuple[str, str]] | None:
    assert component.open_forms is not None
    items_expression = component.open_forms.items_expression
    items_array = jsonLogic(items_expression, data.data, use_var_undefined=True)  # pyright: ignore[reportArgumentType]
    if not items_array:
        return

    audit_log = audit_logger.bind(
        form_id=submission.form.pk,
        component=dump_to_legacy(component),
    )
    if not isinstance(items_array, list):
        audit_log.warning(
            "form_configuration_error",
            error_message=_(
                "Variable obtained with expression {items_expression} for dynamic "
                "options is not an array."
            ).format(items_expression=json.dumps(items_expression)),
        )
        return

    # Remove any None values
    if len(
        not_none_options := [
            item for item in items_array if not is_or_contains_none(item)
        ]
    ) != len(items_array):
        audit_log.warning(
            "form_configuration_error",
            error_message=_(
                "Expression {items_expression} did not return a valid option for "
                "each item."
            ).format(items_expression=json.dumps(items_expression)),
        )

    normalised_options: list[tuple[JSONValue, JSONValue]] = [
        normalise_option(option) for option in not_none_options
    ]

    if any(
        isinstance(item_key, dict | list) or isinstance(item_label, dict | list)
        for item_key, item_label in normalised_options
    ):
        audit_log.warning(
            "form_configuration_error",
            error_message=_(
                "The dynamic options obtained with expression {items_expression} "
                "contain non-primitive types."
            ).format(items_expression=json.dumps(items_expression)),
        )
        return

    escaped_options = [escape_option(option) for option in normalised_options]
    deduplicated_options = deduplicate_options(escaped_options)

    return deduplicated_options


def add_options_to_config(
    component: Radio | Select | Selectboxes,
    data: FormioData,
    submission: Submission,
) -> None:
    # normalize to enum so we still have type-checker help for match exhaustiveness
    data_src = DataSrcOptions(
        component.open_forms.data_src if component.open_forms else "manual"
    )
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
        case DataSrcOptions.manual:
            return
        case _:  # pragma: no cover
            assert_never(data_src)

    options = [
        Option(value=escaped_key, label=escaped_label)
        for escaped_key, escaped_label in items_array
    ]
    # assing to the right property
    match component:
        case Radio() | Selectboxes():
            component.values = options
        case Select():
            component.data.values = options
        case _:  # pragma: no cover
            assert_never(component)
