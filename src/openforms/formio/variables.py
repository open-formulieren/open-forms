import logging

from django.template import TemplateSyntaxError

from openforms.template import render_from_string
from openforms.typing import DataMapping, JSONObject, JSONValue

from .utils import iter_components

logger = logging.getLogger(__name__)


SUPPORTED_TEMPLATE_PROPERTIES = (
    "label",
    "legend",
    "defaultValue",
    "description",
    "html",
    "placeholder",
)


def render(formio_bit: JSONValue, context: dict) -> JSONValue:
    """
    Take a formio property value and evaluate the templates inside.

    The ``formio_bit`` may be a string to be used as template, another JSON primitive
    that we can't pass through the template engine or a complex JSON object to
    recursively render.

    Returns the same datatype as the input datatype, which should be ready for
    JSON serialization.
    """
    # string primitive - we can throw it into the template engine
    if isinstance(formio_bit, str):
        return render_from_string(formio_bit, context)

    # collection - map every item recursively
    if isinstance(formio_bit, list):
        return [render(nested_bit, context) for nested_bit in formio_bit]

    # mapping - map every key/value pair recursively
    if isinstance(formio_bit, dict):
        return {
            key: render(nested_bit, context) for key, nested_bit in formio_bit.items()
        }

    # other primitive or complex object - we can't template this out, so return it
    # unmodified.
    return formio_bit


def inject_variables(configuration: JSONObject, values: DataMapping) -> None:
    """
    Inject the variable values into the Formio configuration.

    Takes a Formio configuration and fully resolved variable state (mapping of variable
    name to its value as a Python object). The configuration is iterated over and every
    component is checked for properties that can be templated. Note that the
    configuration is mutated in the process!

    :arg configuration: A dictionary containing the static Formio configuration (from
      the form designer)
    :arg values: A mapping of variable key to its value (Python native objects)
    :returns: None - this function mutates the datastructures in place

    .. todo:: Support getting non-string based configuration from variables, such as
       `validate.required` etc.
    """
    for component in iter_components(configuration=configuration, recursive=True):
        for property_name in SUPPORTED_TEMPLATE_PROPERTIES:
            property_value = component.get(property_name)
            if not property_value:
                continue

            try:
                templated_value = render(property_value, values)
            except TemplateSyntaxError as exc:
                logger.debug(
                    "Error during formio configuration 'template' rendering",
                    exc_info=exc,
                )
                # return the original config instead
                return property_value
            component[property_name] = templated_value
