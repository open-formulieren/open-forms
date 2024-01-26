from django import template

from openforms.typing import JSONPrimitive

register = template.Library()


class InvalidInput(Exception):
    pass


def extract_tokens(node: dict, prefix: str | None = None) -> dict[str, JSONPrimitive]:
    if not isinstance(node, dict):
        raise InvalidInput(
            "The node is not a dict, can't extract a value or nested keys."
        )

    tokens = {}

    # if a value is found, we have built up the entire token name and can return
    # the name + value combination
    if "value" in node:
        tokens[prefix] = node["value"]
        return tokens

    # if nothing is found, we need to recurse and a node could contain multiple keys
    for key, value in node.items():
        new_prefix = f"{prefix}-{key}" if prefix else f"--{key}"
        try:
            tokens.update(extract_tokens(value, new_prefix))
        except InvalidInput:
            continue  # just ignore invalid input and prevent infinite recursion

    return tokens


@register.simple_tag()
def style_dictionary(styles: dict) -> dict[str, JSONPrimitive]:
    """
    Transform a style dictionary into a mapping of resolved design tokens.
    """
    tokens = extract_tokens(styles)
    return tokens
