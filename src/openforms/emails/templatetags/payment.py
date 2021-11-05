from django import template
from django.template.loader import get_template

register = template.Library()


@register.simple_tag(takes_context=True)
def payment_information(context):
    if context.get("rendering_text"):
        name = "payment_information.txt"
    else:
        name = "payment_information.html"
    return get_template(name).render(context.flatten())
