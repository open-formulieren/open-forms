from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def optional_node(tag, value, hide_empty=True):
    if not value:
        if hide_empty:
            return ""
        else:
            return format_html(
                "<{tag}>{value}</{tag}>\n",
                tag=mark_safe(tag),
                value=value,
            )

    return format_html(
        "<{tag}>{value}</{tag}>\n",
        tag=mark_safe(tag),
        value=value,
    )
