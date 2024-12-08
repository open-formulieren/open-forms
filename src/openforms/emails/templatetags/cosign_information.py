from typing import NotRequired, TypedDict

from django import template
from django.template.loader import render_to_string

from openforms.submissions.models import Submission

register = template.Library()


class CosignInformationContext(TypedDict):
    _submission: Submission
    rendering_text: NotRequired[bool]


@register.simple_tag(takes_context=True)
def cosign_information(context: CosignInformationContext) -> str:
    submission = context["_submission"]
    if not (cosign := submission.cosign_state).is_required:
        return ""

    if context.get("rendering_text"):
        template_name = "emails/templatetags/cosign_information.txt"
    else:
        template_name = "emails/templatetags/cosign_information.html"

    tag_context = {
        "cosign_complete": cosign.is_signed,
        "waiting_on_cosign": cosign.is_waiting,
        "cosigner_email": cosign.email,
    }
    return render_to_string(template_name, tag_context)
