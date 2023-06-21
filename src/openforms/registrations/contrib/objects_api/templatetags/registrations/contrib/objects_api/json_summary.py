import json

from django import template
from django.utils.safestring import SafeString

from openforms.formio.rendering.structured import render_json

register = template.Library()


@register.simple_tag(takes_context=True)
def json_summary(context):
    submission = context.get("_submission")
    if not submission:
        return {}

    get_json_renderer = render_json(submission)
    return SafeString(json.dumps(get_json_renderer))
