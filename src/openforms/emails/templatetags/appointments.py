from django import template
from django.template.loader import render_to_string

from openforms.appointments.utils import get_plugin

register = template.Library()


@register.simple_tag(takes_context=True)
def appointment_information(context):
    appointment_id = context.get("_appointment_id")
    # Use get since _appointment_id could be an empty string
    if not appointment_id:
        return ""

    if context.get("rendering_text"):
        template_name = "emails/templatetags/appointment_information.txt"
    else:
        template_name = "emails/templatetags/appointment_information.html"

    plugin = get_plugin()

    tag_context = {
        "appointment": plugin.get_appointment_details(appointment_id),
        "appointment_cancel_link": plugin.get_cancel_link(context["_submission"]),
        "appointment_change_link": plugin.get_change_link(context["_submission"]),
    }
    return render_to_string(template_name, tag_context)
