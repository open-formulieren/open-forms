import logging

from django.template import TemplateSyntaxError
from django.template.backends.django import DjangoTemplates

from openforms.submissions.logic.datastructures import DataMapping
from openforms.typing import JSONObject

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
        },
    }
)


def render(source: str, context: dict) -> str:
    template = template_engine.from_string(source)
    return template.render(context)


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
