from django.utils.html import escape

from openforms.typing import JSONValue


def escape_html_manually(input: dict) -> dict[str, JSONValue]:
    """
    Used optionally (based on ESCAPE_REGISTRATION_OUTPUT env setting) in order
    to perform HTML escaping before we send the data to the Objects API.
    """
    if not isinstance(input, dict):
        return {}

    for key, value in input.items():
        if isinstance(value, str):
            input[key] = escape(value)
        elif isinstance(value, dict):
            escape_html_manually(value)
    return input
