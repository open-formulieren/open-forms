import json

from django import template
from django.conf import settings
from django.utils.safestring import SafeString

from openforms.formio.rendering.structured import render_json
from openforms.registrations.contrib.objects_api.utils import escape_html_manually

register = template.Library()


@register.simple_tag(takes_context=True)
def uploaded_attachment_urls(context):
    """
    Output a sequence of attachment URLs as a JSON-serialized list.
    """
    # attachments is a list of URLs
    attachments = context.get("submission", {}).get("uploaded_attachment_urls", [])
    return SafeString(json.dumps(attachments))


@register.simple_tag(takes_context=True)
def json_summary(context):
    submission = context.get("_submission")
    if not submission:
        return {}

    json_data = render_json(submission)

    if settings.ESCAPE_REGISTRATION_OUTPUT:
        json_data = escape_html_manually(json_data)

    return SafeString(json.dumps(json_data))
