from django.template import Library
from django.utils.html import format_html_join

register = Library()


@register.simple_tag
def render_spacers(amount: int = 0, classname: str = "") -> str:
    if amount <= 0:
        return ""
    markup = '<span class="{}"></span>'
    args_generator = ((classname,) for _ in range(amount))
    return format_html_join("", markup, args_generator)
