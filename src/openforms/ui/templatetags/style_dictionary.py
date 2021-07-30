from typing import Dict

from django import template

register = template.Library()


def style_dictionary(input: dict, prefix: str = "of") -> Dict[str, str]:
    """
    Transform a style dictionary into a mapping of resolved design tokens.
    """
