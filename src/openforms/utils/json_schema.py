from openforms.typing import JSONObject


def to_multiple(schema: JSONObject) -> JSONObject:
    """Convert a JSON schema of a component to a schema of multiple components.

    :param schema: JSON schema of a component.
    :returns: JSON schema of multiple components.
    """
    title = schema.pop("title")
    return {
        "title": title,
        "type": "array",
        "items": schema,
    }
