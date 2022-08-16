import logging
from typing import Union

from django.template import TemplateSyntaxError
from django.template.backends.django import DjangoTemplates

from openforms.submissions.logic.datastructures import DataMapping
from openforms.typing import JSONObject, JSONPrimitive, JSONValue

from .utils import iter_components

logger = logging.getLogger(__name__)


SUPPOORTED_TEMPLATE_PROPERTIES = (
    "label",
    "legend",
    "defaultValue",
    "description",
    "html",
    "placeholder",
)


# TODO: move to separate utility for sandboxed rendering!
class SandboxedDjangoTemplates(DjangoTemplates):
    def get_templatetag_libraries(self, custom_libraries):
        return {}


# statically configured engine without access to templates on the filesystem
template_engine = SandboxedDjangoTemplates(
    params={
        "NAME": "django_sandboxed",
        "DIRS": [],  # no file system paths to look up files (also blocks {% include %} etc)
        "APP_DIRS": False,
        "OPTIONS": {
            "autoescape": True,
            "libraries": [],  # no access to our custom template tags
            "builtins": [
                "django.templatetags.l10n",  # allow usage of localize/unlocalize
            ],
        },
    }
)


def _render(source: str, context: dict) -> str:
    template = template_engine.from_string(source)
    return template.render(context)


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
        return _render(formio_bit, context)

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
    :arg values: A mapping of variable name to its value (Python native objects)
    :returns: None - this function mutates the datastructures in place

    .. todo:: Support getting non-string based configuration from variables, such as
       `validate.required` etc.
    """
    for component in iter_components(configuration=configuration, recursive=True):
        for property_name in SUPPOORTED_TEMPLATE_PROPERTIES:
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
