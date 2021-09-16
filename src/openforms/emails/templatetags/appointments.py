from django import template

from openforms.appointments.utils import get_client

register = template.Library()


@register.simple_tag(takes_context=True)
def appointment_information(context):
    if not (appointment_id := context.get("_appointment_id")):
        # Use get since _appointment_id could be an empty string
        return ""

    client = get_client()
    return client.get_appointment_details_html(appointment_id)


@register.simple_tag(takes_context=True)
def get_appointment_links(context):
    client = get_client()
    return client.get_appointment_links(context["_submission"])
