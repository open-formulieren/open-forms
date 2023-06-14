from django import template
from django.template.loader import render_to_string

register = template.Library()


@register.simple_tag(takes_context=True)
def cosign_info(context):
    submission = context["_submission"]

    if context.get("rendering_text"):
        template_name = "emails/templatetags/cosign_info.txt"
    else:
        template_name = "emails/templatetags/cosign_info.html"

    tag_context = {
        "cosign_complete": submission.cosign_complete,
        "waiting_on_cosign": submission.waiting_on_cosign,
        "cosigner_email": submission.cosigner_email,
    }
    return render_to_string(template_name, tag_context)
