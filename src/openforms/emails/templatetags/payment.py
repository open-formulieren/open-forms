from django import template
from django.template.loader import render_to_string

register = template.Library()


@register.simple_tag(takes_context=True)
def payment_information(context):
    if context.get("rendering_text"):
        template_name = "emails/templatetags/payment_information.txt"
    else:
        template_name = "emails/templatetags/payment_information.html"

    return render_to_string(template_name, context.flatten())
