import json

from django import template
from django.conf import settings
from django.utils.safestring import SafeString

from openforms.formio.rendering.structured import render_json
from openforms.registrations.contrib.objects_api.utils import html_escape_json

register = template.Library()


@register.simple_tag(takes_context=True)
def uploaded_attachment_urls(context: template.Context) -> SafeString:
    """
    Output a sequence of attachment URLs as a JSON-serialized list.
    """
    attachments = context.get("submission", {}).get("uploaded_attachment_urls", [])
    return SafeString(json.dumps(attachments))


@register.simple_tag(takes_context=True)
def json_summary(context: template.Context) -> SafeString | dict:
    submission = context.get("_submission")
    if not submission:
        return {}

    json_data = render_json(submission)

    if settings.ESCAPE_REGISTRATION_OUTPUT:
        json_data = html_escape_json(json_data)

    return SafeString(json.dumps(json_data))


@register.simple_tag
def as_geo_json(value: list[float] | str) -> SafeString | dict:
    """Output the ``value`` as a safe GeoJSON dumped string.

    As of today, this only supports coordinates. This essentially does the same thing as
    :func:`_transform_coordinates`, but for any map component.
    """
    if not value:
        return {}
    data = {"type": "Point", "coordinates": [value[0], value[1]]}

    return SafeString(json.dumps(data))
