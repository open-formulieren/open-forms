from django import template
from django.template.loader import render_to_string

from openforms.appointments.service import (
    AppointmentRenderer,
    get_appointment,
    get_plugin,
)
from openforms.submissions.rendering.constants import RenderModes

register = template.Library()


@register.simple_tag(takes_context=True)
def appointment_information(context):
    # Use get since _appointment_id could be an empty string
    if not (appointment_id := context.get("_appointment_id")):
        return ""

    if as_text := context.get("rendering_text", False):
        template_name = "emails/templatetags/appointment_information.txt"
    else:
        template_name = "emails/templatetags/appointment_information.html"

    # check for appointments
    submission = context["_submission"]
    appointment = get_appointment(submission)

    assert appointment
    plugin_id = appointment.plugin

    plugin = get_plugin(plugin=plugin_id)

    tag_context = {
        "appointment": plugin.get_appointment_details(appointment_id),
        "appointment_renderer": AppointmentRenderer(
            submission=submission,
            mode=RenderModes.confirmation_email,
            as_html=not as_text,
        ),
        "appointment_cancel_link": plugin.get_cancel_link(context["_submission"]),
    }
    return render_to_string(template_name, tag_context)
