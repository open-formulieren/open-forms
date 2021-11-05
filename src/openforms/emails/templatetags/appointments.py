from django import template
from django.template.loader import get_template

from openforms.appointments.utils import get_client

register = template.Library()


@register.simple_tag(takes_context=True)
def appointment_information(context):
    appointment_id = context.get("_appointment_id")
    # Use get since _appointment_id could be an empty string
    if not appointment_id:
        return ""

    client = get_client()
    return client.get_appointment_details_markup(
        appointment_id, as_text=context.get("rendering_text")
    )


@register.simple_tag(takes_context=True)
def appointment_links(context):
    if context.get("rendering_text"):
        name = "appointment_links.txt"
    else:
        name = "appointment_links.html"

    client = get_client()
    tag_context = {
        "appointment_links": client.get_appointment_links(context["_submission"]),
    }
    return get_template(name).render(tag_context)
