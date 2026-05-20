from django.utils.html import escape

from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.typing import VariableValue


def recursively_escape_html_strings[T: VariableValue](value: T) -> T:
    """
    Recursively apply HTML escaping to string value nodes.
    """
    match value:
        case list():
            return [recursively_escape_html_strings(item) for item in value]  # pyright: ignore[reportReturnType]
        case dict():
            return {
                key: recursively_escape_html_strings(value)
                for key, value in value.items()
            }  # pyright: ignore[reportReturnType]
        case str():
            return escape(value)
        case _:
            # nothing to do, return unmodified
            return value


def apply_defaults_to(config_group: ObjectsAPIGroupConfig, options) -> None:
    options.setdefault("version", 1)
    options.setdefault("organisatie_rsin", config_group.organisatie_rsin)
