import logging
from typing import Callable, Iterator

from django.template import TemplateSyntaxError

from openforms.template import parse, render_from_string
from openforms.typing import DataMapping, JSONObject, JSONValue

from .datastructures import FormioConfigurationWrapper
from .typing import Component
from .utils import flatten_by_path

logger = logging.getLogger(__name__)


SUPPORTED_TEMPLATE_PROPERTIES = (
    "label",
    "groupLabel",  # component-type: editgrid
    "legend",
    "defaultValue",
    "description",
    "html",
    "placeholder",
    "values",  # component-types: radio/selectBoxes
    "data",  # component-type: select
    "tooltip",
)


def _recursive_apply(formio_bit: JSONValue, func: Callable, *args, **kwargs):
    """
    Take a formio property value and recursively apply ``func`` to it.

    The ``formio_bit`` may be a string to be used as template, another JSON primitive
    that we can't pass through the template engine or a complex JSON object to
    recursively render.

    Returns the same datatype as the input datatype, which should be ready for
    JSON serialization.
    """
    # string primitive - we can throw it into the template engine
    if isinstance(formio_bit, str):
        return func(formio_bit, *args, **kwargs)

    # collection - map every item recursively
    if isinstance(formio_bit, list):
        return [
            _recursive_apply(nested_bit, func, *args, **kwargs)
            for nested_bit in formio_bit
        ]

    # mapping - map every key/value pair recursively
    if isinstance(formio_bit, dict):
        return {
            key: _recursive_apply(nested_bit, func, *args, **kwargs)
            for key, nested_bit in formio_bit.items()
        }

    # other primitive or complex object - we can't template this out, so return it
    # unmodified.
    return formio_bit


def render(formio_bit: JSONValue, context: dict) -> JSONValue:
    return _recursive_apply(formio_bit, render_from_string, context=context)


def iter_template_properties(component: Component) -> Iterator[tuple[str, JSONValue]]:
    """
    Return an iterator over the formio component properties that are template-enabled.

    Each item returns a tuple with the key and value of the formio component.
    """
    for property_name in SUPPORTED_TEMPLATE_PROPERTIES:
        property_value = component.get(property_name)
        yield (property_name, property_value)


def validate_configuration(configuration: JSONObject) -> dict[str, str]:
    """
    Check the Formio configuration for template syntax errors.

    Returns a mapping of component key and (json) path of the component within the
    configuration for the components that have template syntax errors.
    """
    flattened_components = flatten_by_path(configuration)

    errored_components = {}
    for path, component in flattened_components.items():
        for property_name, property_value in iter_template_properties(component):
            try:
                _recursive_apply(property_value, parse)
            except TemplateSyntaxError:
                errored_components[component["key"]] = f"{path}.{property_name}"
    return errored_components


def inject_variables(
    configuration: FormioConfigurationWrapper,
    values: DataMapping,
    translate: Callable[[str], str] = str,
) -> None:
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
    for component in configuration:
        for property_name, property_value in iter_template_properties(component):
            if not property_value:
                continue

            match property_value:
                case str():
                    property_value = translate(property_value)
                case [str(), *_]:
                    property_value = [
                        translate(s) for s in property_value if isinstance(s, str)
                    ]
                case [{"label": _}, *_]:
                    for item in property_value:
                        if "label" in item:
                            item["label"] = translate(item["label"])
                case {"values": [*defined_values]}:
                    for item in defined_values:
                        if "label" in item:
                            item["label"] = translate(item["label"])

            try:
                templated_value = render(property_value, values)
            except TemplateSyntaxError as exc:
                logger.debug(
                    "Error during formio configuration 'template' rendering",
                    exc_info=exc,
                )
                # keep the original value on error
                continue

            component[property_name] = templated_value
