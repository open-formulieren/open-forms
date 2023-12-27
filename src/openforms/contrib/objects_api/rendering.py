import json
import sys
from contextlib import contextmanager
from typing import Any

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.template.defaultfilters import filesizeformat

from openforms.template import openforms_backend, render_from_string
from openforms.typing import JSONValue


@contextmanager
def catch_json_decode_errors():
    try:
        yield
    except json.decoder.JSONDecodeError as err:
        raise RuntimeError("Template evaluation did not result in valid JSON") from err


def check_size_stringyfied_json_not_above_limit(content: str) -> None:
    if (data_size := sys.getsizeof(content)) > settings.MAX_UNTRUSTED_JSON_PARSE_SIZE:
        formatted_size = filesizeformat(data_size)
        max_size = filesizeformat(settings.MAX_UNTRUSTED_JSON_PARSE_SIZE)
        raise SuspiciousOperation(
            "Templated out content JSON exceeds the maximum size '%i' (it is %i).",
            max_size,
            formatted_size,
        )


def render_to_json(template: str, context: dict[str, Any]) -> JSONValue:
    """Render the provided template and context into a JSON serializable object"""

    # FIXME: replace with better suited alternative dealing with JSON specifically
    data = render_from_string(
        template,
        context=context,
        disable_autoescape=True,
        backend=openforms_backend,
    )

    check_size_stringyfied_json_not_above_limit(data)

    with catch_json_decode_errors():
        json_data = json.loads(data)

    return json_data
