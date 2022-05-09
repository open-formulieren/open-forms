import warnings
from typing import Any

from django import template
from django.template.loader import get_template
from django.utils.encoding import force_str

from openforms.submissions.rendering.constants import RenderModes
from openforms.submissions.rendering.renderer import Renderer

register = template.Library()


@register.simple_tag(takes_context=True)
def summary(context):
    as_text = context.get("rendering_text")
    renderer = Renderer(
        submission=context["_submission"],
        mode=RenderModes.confirmation_email,
        as_html=not as_text,
    )
    if as_text:
        name = "emails/templatetags/form_summary.txt"
    else:
        name = "emails/templatetags/form_summary.html"
    context["renderer"] = renderer
    return get_template(name).render(context.flatten())


@register.simple_tag()
def whitespace(amount: int, base=" ") -> str:
    return base * amount
