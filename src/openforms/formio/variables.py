from collections.abc import Collection, Iterator, Mapping, Sequence
from dataclasses import dataclass

from django.template import TemplateSyntaxError

import structlog
from typing_extensions import deprecated

from openforms.template import extract_variables_used, parse, render_from_string
from openforms.typing import JSONValue
from openforms.utils.helpers import recursively_apply_function

from .datastructures import FormioConfig, FormioConfigurationWrapper, FormioData
from .typing import Component

logger = structlog.stdlib.get_logger(__name__)

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


def _render_and_force_str(source: str, context: Mapping[str, object]) -> str:
    result = render_from_string(source, context)
    # Slice the SafeString to force it into a normal string.
    return result[:]


def render(formio_bit: JSONValue, context: dict) -> JSONValue:
    return recursively_apply_function(
        formio_bit, _render_and_force_str, context=context
    )


@deprecated("replaced by AnyComponent.iter_template_attributes")
def iter_template_properties(component: Component) -> Iterator[tuple[str, JSONValue]]:
    """
    Return an iterator over the formio component properties that are template-enabled.

    Each item returns a tuple with the key and value of the formio component.
    """

    # no server-side template evaluation here
    if component["type"] == "softRequiredErrors":
        return

    for property_name in SUPPORTED_TEMPLATE_PROPERTIES:
        property_value = component.get(property_name)
        yield (property_name, property_value)


@dataclass
class ComponentTemplateSyntaxError:
    key: str
    label: str
    property_name: str  # one of SUPPORTED_TEMPLATE_PROPERTIES
    parents_representation: str  # E.g. "My fieldset > My editgrid"


def get_configuration_template_syntax_errors(
    components: Sequence[Component],
) -> Collection[ComponentTemplateSyntaxError]:
    """
    Check the Formio configuration for template syntax errors.

    Returns metadata of where template syntax errors occur. It is assumed that the
    component key uniqueness validation happens before or after, to ensure that all
    components are eventually validated.
    """
    errors: list[ComponentTemplateSyntaxError] = []

    formio_config = FormioConfig(name="<in-memory>", components=components)
    for component in formio_config:
        for property_name, property_value in component.iter_template_attributes():
            try:
                recursively_apply_function(property_value, parse)
            except TemplateSyntaxError:
                key = component.key
                parents = formio_config.get_parents(key)
                errors.append(
                    ComponentTemplateSyntaxError(
                        key=key,
                        label=component.get_label(),
                        property_name=property_name,
                        parents_representation=" > ".join(
                            parent.get_label() for parent in parents
                        ),
                    )
                )

    return errors


def inject_variables(
    configuration: FormioConfigurationWrapper, values: FormioData
) -> None:
    """
    Inject the variable values into the Formio configuration.

    Takes a Formio configuration and fully resolved variable state (mapping of variable
    name to its value as a Python object). The configuration is iterated over and every
    component is checked for properties that can be templated. Note that the
    configuration is mutated in the process!

    :param configuration: A dictionary containing the static Formio configuration (from
      the form designer)
    :param values: A mapping of variable key to its value (Python native objects)
    :returns: None - this function mutates the datastructures in place

    .. todo:: Support getting non-string based configuration from variables, such as
       `validate.required` etc.
    """
    for component in configuration:
        for property_name, property_value in iter_template_properties(component):
            if not property_value:
                continue

            match property_value:
                case [str(), *_]:
                    property_value = [s for s in property_value if isinstance(s, str)]

            try:
                templated_value = render(property_value, values.data)
            except TemplateSyntaxError as exc:
                logger.debug(
                    "formio.template_evaluation_failure",
                    template=property_value,
                    exc_info=exc,
                )
                # keep the original value on error
                continue

            component[property_name] = templated_value


def extract_variables_from_template_properties(component: Component) -> set[str]:
    """
    Extract all variables used in the template expressions of the relevant properties.

    Relevant properties: label, groupLabel, legend, defaultValue, description, html,
    placeholder, tooltip, data (select), values (radio and selectboxes).

    :param component: Component to extract variables from.
    :return: Set of variable names, empty if no variables were extracted.
    """
    variables: set[str] = set()
    for _property_name, property_value in iter_template_properties(component):
        recursively_apply_function(
            property_value, lambda v: variables.update(extract_variables_used(v))
        )

    return variables
