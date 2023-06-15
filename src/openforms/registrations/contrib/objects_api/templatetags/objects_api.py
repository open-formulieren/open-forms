import json

from django import template
from django.utils.safestring import SafeString

from openforms.formio.rendering.structured import render_json
from openforms.submissions.models.submission import Submission

register = template.Library()


@register.simple_tag(takes_context=True)
def json_summary(context):
    submission = context.get("_submission")
    if submission:
        get_json_renderer = render_json(submission)
        print(get_json_renderer)
        return SafeString(json.dumps(get_json_renderer))

    return {}
