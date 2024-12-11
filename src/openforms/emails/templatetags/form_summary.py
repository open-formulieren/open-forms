from django import template
from django.template.loader import get_template

from openforms.appointments.service import get_appointment
from openforms.formio.rendering.default import (
    EditGridGroupNode,
    EditGridNode,
    FieldSetNode,
)
from openforms.submissions.rendering.constants import RenderModes
from openforms.submissions.rendering.renderer import Renderer

register = template.Library()


@register.simple_tag(takes_context=True)
def confirmation_summary(context):
    submission = context["_submission"]
    # There are no steps or summary to render in new-style appointment submission
    if get_appointment(submission) is not None:
        return ""

    as_text = context.get("rendering_text", False)
    renderer = Renderer(
        submission=submission,
        mode=RenderModes.confirmation_email,
        as_html=not as_text,
    )
    if as_text:
        name = "emails/templatetags/form_summary.txt"
    else:
        name = "emails/templatetags/form_summary.html"
    context.update(
        {
            "renderer": renderer,
            "bold_label_modifiers": [
                FieldSetNode.layout_modifier,
                EditGridNode.layout_modifier,
                EditGridGroupNode.layout_modifier,
            ],
        }
    )
    return get_template(name).render(context.flatten())


@register.simple_tag()
def whitespace(amount: int, base=" ") -> str:
    return base * amount
