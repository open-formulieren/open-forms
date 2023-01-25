from django.template.defaultfilters import escape_filter as escape

from glom import assign, glom
from json_logic import jsonLogic

from openforms.typing import DataMapping

from ..typing import Component


def add_options_to_config(
    component: Component,
    data: DataMapping,
    options_path: str = "values",
    data_src_path: str = "dataSrc",
) -> None:
    if glom(component, data_src_path, default=None) != "variable":
        return

    items_path = glom(component, "data.itemsExpression")

    # The array of items from which we need to get the values
    items_array = jsonLogic(items_path, data)

    if not items_array or len(items_array) == 0:
        return

    # Is each item a dict, like for repeating groups, or are they primitives
    # ready to use?
    is_obj = isinstance(items_array[0], dict)

    if not is_obj:
        values = []
        for value in items_array:
            # value is user input!
            escaped_value = escape(value)
            values.append({"label": escaped_value, "value": escaped_value})

        assign(
            component,
            options_path,
            values,
            missing=dict,
        )
        return

    values = []
    value_path = glom(component, "data.valueExpression", default=None)

    # Case in which the form designer didn't configure the valueExpression by mistake.
    # Catching this in validation on creation of the form definition is tricky, because the referenced component may
    # be in another form definition.
    if not value_path:
        return

    for item in items_array:
        value = jsonLogic(value_path, item)
        # value is user input!
        escaped_value = escape(value)
        values.append({"label": escaped_value, "value": escaped_value})

    assign(component, options_path, values, missing=dict)
