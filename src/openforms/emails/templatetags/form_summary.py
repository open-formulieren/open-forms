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


@register.simple_tag(takes_context=True)
def display_value(context, value: Any):
    warnings.warn(
        "The {% display_value %} template tag is deprecated, please use "
        "'openforms.submissions.rendering.renderer.Renderer' instead.",
        DeprecationWarning,
    )
    _is_html = not context.get("rendering_text", False)
    if isinstance(value, dict) and value.get("originalName"):
        # uploads
        return value["originalName"]
    if isinstance(value, (list, tuple)):
        return "; ".join(display_value(context, v) for v in filter(None, value))

    # output - see if we have something that can output as html and as plain text
    method = "as_html" if _is_html else "as_plain_text"
    formatter = getattr(value, method, None)
    if formatter is not None and callable(formatter):
        return formatter()

    if value is None:
        return ""
    else:
        # fall back to default of string representation
        return force_str(value)
