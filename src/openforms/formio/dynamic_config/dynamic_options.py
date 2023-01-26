from django.template.defaultfilters import escape_filter as escape

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
    data_src_path: str = "dataSrc",
) -> None:
    if glom(component, data_src_path, default=None) != "variable":
        return

    items_path = glom(component, "data.itemsExpression")

    # The array of items from which we need to get the values
    items_array = jsonLogic(items_path, data)

    if not items_array:
        return

    # Is each item a dict, like for repeating groups, or are they primitives
    # ready to use?
    is_obj = isinstance(items_array[0], dict)

    if is_obj:
        value_path = glom(component, "data.valueExpression", default=None)
        # Case in which the form designer didn't configure the valueExpression by mistake.
        # Catching this in validation on creation of the form definition is tricky, because the referenced component may
        # be in another form definition.
        if not value_path:
            logevent.form_configuration_error(submission.form, component)
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
