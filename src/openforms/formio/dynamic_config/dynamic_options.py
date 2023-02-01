import json

from django.template.defaultfilters import escape_filter as escape
from django.utils.datastructures import OrderedSet
from django.utils.translation import gettext as _

from glom import assign, glom
from json_logic import jsonLogic

from openforms.logging import logevent
from openforms.submissions.models import Submission
from openforms.typing import DataMapping

from ..typing import Component


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

    if any([isinstance(item, (list, dict)) for item in items_array]):
        logevent.form_configuration_error(
            submission.form,
            component,
            _(
                "The dynamic options obtained with expression %(items_expression)s contain non-primitive types."
            )
            % {"items_expression": json.dumps(items_expression)},
        )
        return

    # Remove any None values
    if None in items_array:
        logevent.form_configuration_error(
            submission.form,
            component,
            _(
                "Expression %(items_expression)s did not return a valid option for each item."
            )
            % {"items_expression": json.dumps(items_expression)},
        )
        items_array = [item for item in items_array if item is not None]

    # items_array contains user input! We also don't want duplicate values
    escaped_values = OrderedSet(map(escape, items_array))
    assign(
        component,
        options_path,
        [
            {"label": escaped_value, "value": escaped_value}
            for escaped_value in escaped_values
        ],
        missing=dict,
    )
