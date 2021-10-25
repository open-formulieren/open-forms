import logging
import re
from functools import partial
from html import unescape
from typing import Any, List, Optional, Sequence, Tuple
from urllib.parse import urlparse, urlsplit

from django.conf import settings
from django.template.loader import get_template
from django.utils.html import strip_tags as django_strip_tags

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
    html_body: str,
    from_email: str,
    recipient_list: List[str],
    attachment_tuples: AttachmentsType = None,
    fail_silently: bool = False,
    text_message: str = None,
) -> None:
    # sanitize
    html_body = sanitize_content(html_body)

    # render versions
    if not text_message:
        text_message = strip_tags_plus(html_body)

    template = get_template("emails/wrapper.html")
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


NEWLINE_CHARS = (
    "\n",
    "\r",
    "\r\n",
    "\v",
    "\x0b",
    "\f",
    "\x0c",
    "\x1c",
    "\x1d",
    "\x1e",
    "\x85",
    "\u2028",
    "\u2029",
)


def strip_tags_plus(text):
    # copied and modified from https://bitbucket.org/maykinmedia/werkbezoek/src/develop/src/werkbezoek/utils/email.py
    text = unwrap_anchors(text)
    text = django_strip_tags(text)
    lines = text.splitlines()
    transformed_lines = transform_lines(lines)
    deduplicated_newlines = deduplicate_newlines(transformed_lines)

    return "".join(deduplicated_newlines)


def transform_lines(lines):
    transformed_lines = []

    for line in lines:
        stripped_line = unescape(line)
        splitted_line = f"{' '.join(stripped_line.split())}".rstrip()

        transformed_lines.append(f"{splitted_line}\n")

    return transformed_lines


def deduplicate_newlines(lines):
    deduplicated_newlines = []

    for line in lines:
        if not deduplicated_newlines:
            deduplicated_newlines.append(line)
            continue

        is_newline = line in NEWLINE_CHARS

        if is_newline and deduplicated_newlines[-1] in NEWLINE_CHARS:
            continue

        deduplicated_newlines.append(line)

    return deduplicated_newlines


def unwrap_anchors(html_str):
    """
    ugly util to append the href inside the anchor text so we can use strip-tags
    """
    from lxml.html import fromstring, tostring

    root = fromstring(html_str)

    for link in root.xpath("//a"):
        url = link.attrib.get("href", None)
        if not url:
            continue
        link.text += f" ({url})"

    return tostring(root, encoding="utf8").decode("utf8")
