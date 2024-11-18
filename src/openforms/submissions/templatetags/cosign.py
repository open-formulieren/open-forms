from textwrap import dedent

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from openforms.frontend import get_frontend_redirect_url
from openforms.typing import StrOrPromise

from ..models import Submission

register = template.Library()


@register.simple_tag(takes_context=True)
def cosign_button(context, text: StrOrPromise = _("Cosign now")):
    """
    Render a link/button to start the cosign process.
    """
    submission: Submission = context["_submission"]
    url = get_frontend_redirect_url(
        submission,
        action="cosign-init",
        action_params={"code": submission.public_registration_reference},
    )
    template = dedent(
        """
        <a href="{href}">
            <button class="utrecht-button utrecht-button--primary-action" type="button">
                {text}
            </button>
        </a>
    """
    )
    return format_html(template, href=mark_safe(url), text=text)
