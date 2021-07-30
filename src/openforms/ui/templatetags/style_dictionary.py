from typing import Dict, Union

from django import template

register = template.Library()

JSONPrimitive = Union[str, int, float, None]


class InvalidInput(Exception):
    pass


def extract_tokens(prefix: str, node: dict) -> Dict[str, JSONPrimitive]:
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
        new_prefix = f"{prefix}-{key}"
        try:
            tokens.update(extract_tokens(new_prefix, value))
        except InvalidInput:
            continue  # just ignore invalid input and prevent infinite recursion

    return tokens


@register.simple_tag()
def style_dictionary(styles: dict, prefix: str = "of") -> Dict[str, JSONPrimitive]:
    """
    Transform a style dictionary into a mapping of resolved design tokens.
    """
    tokens = extract_tokens(f"--{prefix}", styles)
    return tokens
