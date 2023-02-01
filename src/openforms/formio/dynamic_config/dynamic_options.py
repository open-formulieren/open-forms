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

    items_path = glom(component, "openForms.itemsExpression")

    # The array of items from which we need to get the values
    items_array = jsonLogic(items_path, data)
    if not items_array:
        return

    if not isinstance(items_array, list):
        logevent.form_configuration_error(
            submission.form,
            component,
            _(
                "Variable obtained with expression %(items_path)s for dynamic options is not an array."
            )
            % {"items_path": json.dumps(items_path)},
        )
        return

    value_path = glom(component, "openForms.valueExpression", default=None)
    if not value_path and any([isinstance(item, (list, dict)) for item in items_array]):
        logevent.form_configuration_error(
            submission.form,
            component,
            _(
                "The choices for component %(label)s (%(key)s) are improperly configured. "
                "The JSON logic expression to retrieve the items is configured, but no expression for the items "
                "values was configured."
            )
            % {"label": component["label"], "key": component["key"]},
        )
        return

    if value_path:
        items_array = map(lambda item: jsonLogic(value_path, item), items_array)

    # Remove any None values
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
