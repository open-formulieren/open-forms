from django import template
from django.template.loader import get_template

register = template.Library()


@register.simple_tag(takes_context=True)
def registration_summary(context):
    as_text = context.get("rendering_text")
    if as_text:
        name = "registrations/contrib/email/registration_summary.txt"
    else:
        name = "registrations/contrib/email/registration_summary.html"

    return get_template(name).render(context.flatten())
