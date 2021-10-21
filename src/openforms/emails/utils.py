import logging
import re
from functools import partial
from typing import Any, List, Optional, Sequence, Tuple
from urllib.parse import urlparse, urlsplit

from django.conf import settings
from django.template.loader import get_template
from django.utils.html import strip_tags

from openforms.config.models import GlobalConfiguration

from ..utils.email import send_mail_plus
from .constants import URL_REGEX
from .context import get_wrapper_context

logger = logging.getLogger(__name__)


def sanitize_urls(allowlist: List[str], match) -> str:
    parsed = urlparse(match.group())
    if parsed.netloc in allowlist:
        return match.group()

    logger.debug("Sanitized URL from email: %s", match.group())
    return ""


def get_system_netloc_allowlist():
    return [
        # add the BASE_URL to allow o.a. payments and appointments to link back
        urlsplit(settings.BASE_URL).netloc,
    ]


def sanitize_content(content: str) -> str:
    """
    Sanitize the content by stripping untrusted content.

    This function is meant to protect against untrusted user input in e-mail bodies. It
    performs the following sanitizations:

    * strip URLs that are not present in the explicit allow list
    """
    config = GlobalConfiguration.get_solo()

    # strip out any hyperlinks that are not in the configured allowlist
    allowlist = get_system_netloc_allowlist() + config.email_template_netloc_allowlist
    replace_urls = partial(sanitize_urls, allowlist)
    stripped = re.sub(URL_REGEX, replace_urls, content)

    return stripped


AttachmentsType = Optional[Sequence[Tuple[str, str, Any]]]


def send_mail_html(
    subject: str,
    recipient_list: List[str],
    from_email: str,
    html_body: str,
    attachment_tuples: AttachmentsType = None,
    fail_silently: bool = False,
) -> None:

    template = get_template("emails/wrapper.html")

    # sanitize
    html_body = sanitize_content(html_body)

    # render versions
    # TODO swap django strip_tags for werkbezoek strip_tags
    text_message = strip_tags(html_body)

    wrapper_context = get_wrapper_context(html_body)
    html_message = template.render(wrapper_context)

    send_mail_plus(
        subject,
        text_message,
        from_email,  # TODO: add config option to specify sender e-mail
        recipient_list,
        html_message=html_message,
        fail_silently=fail_silently,
        attachments=attachment_tuples,
    )
