import json

from django.template.defaultfilters import escape_filter as escape
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

    # Is each item a dict, like for repeating groups, or are they primitives
    # ready to use?
    is_obj = isinstance(items_array[0], dict)

    if is_obj:
        value_path = glom(component, "openForms.valueExpression", default=None)
        # Case in which the form designer didn't configure the valueExpression by mistake.
        # Catching this in validation on creation of the form definition is tricky, because the referenced component may
        # be in another form definition.
        if not value_path:
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

        items_array = [jsonLogic(value_path, item) for item in items_array]

    # items_array contains user input!
    escaped_values = map(escape, items_array)
    assign(
        component,
        options_path,
        [
            {"label": escaped_value, "value": escaped_value}
            for escaped_value in escaped_values
        ],
        missing=dict,
    )
