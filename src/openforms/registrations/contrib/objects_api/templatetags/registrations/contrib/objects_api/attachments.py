from django import template
from django.utils.safestring import SafeString

from openforms.template import openforms_backend, render_from_string

register = template.Library()


@register.simple_tag(takes_context=True)
def attachments(context):
    # attachments is a list of URLs
    attachments = context.get("submission", {}).get("attachments", [])

    attachments_template = """
    [{% for attachment in attachments %}"{{ attachment }}"{% if not forloop.last %},{% endif %}{% endfor %}]
    """

    rendered_attachments = render_from_string(
        attachments_template,
        context={"attachments": attachments},
        disable_autoescape=True,
        backend=openforms_backend,
    )
    return SafeString(rendered_attachments.strip())
