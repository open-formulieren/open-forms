import json

from django import template
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import SafeString

from openforms.formio.rendering.structured import (
    reshape_submission_data_for_json_summary,
)
from openforms.registrations.contrib.objects_api.utils import (
    recursively_escape_html_strings,
)
from openforms.typing import JSONEncodable

from .....handlers.v1 import SubmissionContext

register = template.Library()


@register.simple_tag(takes_context=True)
def uploaded_attachment_urls(context: template.Context) -> SafeString:
    """
    Output a sequence of attachment URLs as a JSON-serialized list.
    """
    submission_context: SubmissionContext | None = context.get("submission")
    attachments = (
        submission_context["uploaded_attachment_urls"] if submission_context else []
    )
    return as_json(attachments)


@register.simple_tag(takes_context=True)
def json_summary(context: template.Context) -> SafeString:
    submission = context.get("_submission")

    data = reshape_submission_data_for_json_summary(submission) if submission else {}

    if settings.ESCAPE_REGISTRATION_OUTPUT:
        data = recursively_escape_html_strings(data)

    return SafeString(json.dumps(data, cls=DjangoJSONEncoder))


@register.simple_tag
def as_geo_json(value: list[float] | str) -> SafeString:
    """Output the ``value`` as a safe GeoJSON dumped string.

    As of today, this only supports coordinates. This essentially does the same thing as
    :func:`_transform_coordinates`, but for any map component.
    """
    data = (
        {
            "type": "Point",
            "coordinates": [value[0], value[1]],
        }
        if value
        else {}
    )

    return as_json(data)


@register.simple_tag
def as_json(value: JSONEncodable):
    """
    Dump the value as a JSON string.

    DO NOT USE THIS OUTSIDE OF OBJECTS API REGISTRATION TEMPLATES. It is unsafe. The
    objects API templates validate that the result can be loaded as JSON.
    """
    return SafeString(json.dumps(value))
