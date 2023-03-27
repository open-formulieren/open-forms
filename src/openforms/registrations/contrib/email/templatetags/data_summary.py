from django import template
from django.template.loader import get_template

register = template.Library()


@register.simple_tag(takes_context=True)
def data_summary(context):
    as_text = context.get("rendering_text")
    if as_text:
        name = "emails/data_summary.txt"
    else:
        name = "emails/data_summary.html"

    return get_template(name).render(context.flatten())
