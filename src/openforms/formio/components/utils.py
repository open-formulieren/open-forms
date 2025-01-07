from django.utils.crypto import salted_hmac

from openforms.typing import JSONObject

from ..typing import Component

def _normalize_pattern(pattern: str) -> str:
    """
    Normalize a regex pattern so that it matches from beginning to the end of the value.
    """
    if not pattern.startswith("^"):
        pattern = f"^{pattern}"
    if not pattern.endswith("$"):
        pattern = f"{pattern}$"
    return pattern


def salt_location_message(message_bits: dict[str, str]) -> str:
    """
    Put an extra layer of protection and make sure that the value is not tampered with.
    """
    computed_message = f"{message_bits['postcode']}/{message_bits['number']}/{message_bits['city']}/{message_bits['street_name']}"
    computed_hmac = salted_hmac("location_check", value=computed_message).hexdigest()
    return computed_hmac


def to_multiple(schema: JSONObject) -> JSONObject:
    """Convert a JSON schema of a component to a schema of multiple components.

    :param schema: JSON schema of a component.
    :returns: JSON schema of multiple components.
    """
    title = f"Array of '{schema.pop("title")}'"
    return {
        "title": title,
        "type": "array",
        "items": schema,
    }


def handle_component_properties(base: JSONObject, component: Component) -> JSONObject:
    """Handle component JSON schema properties by:

    - Evaluating the 'multiple' property of the component, and adjust the schema
    accordingly.

    :param base: Base JSON schema properties of a component.
    :param component: Component.

    :returns: Handled JSON schema.
    """
    multiple = component.get("multiple", False)
    return to_multiple(base) if multiple else base
