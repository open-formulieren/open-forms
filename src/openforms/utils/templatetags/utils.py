"""
Warning!

Any template tag added to this file will automatically be added to the 'sandboxed' Django templates backend.
"""

from django import template

register = template.Library()


@register.simple_tag(name="get_value")
def get_value(value: dict, value_key: str) -> str:
    if not isinstance(value, dict):
        return ""

    return str(value.get(value_key, ""))
