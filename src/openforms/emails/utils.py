import logging
import re
from functools import partial
from html import unescape
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse, urlsplit

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.template import Context, Template
from django.template.defaultfilters import date as date_filter
from django.template.loader import get_template
from django.urls import reverse
from django.utils.html import strip_tags as django_strip_tags

from lxml.html import fromstring, tostring

from openforms.appointments.models import AppointmentInfo
from openforms.config.models import GlobalConfiguration
from openforms.utils.email import send_mail_plus
from openforms.utils.urls import build_absolute_uri

from .constants import URL_REGEX
from .context import get_wrapper_context

logger = logging.getLogger(__name__)

MESSAGE_SIZE_LIMIT = 2 * 1024 * 1024

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


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
    # render versions
    if not text_message:
        text_message = strip_tags_plus(html_body)

    # sanitize
    html_body = sanitize_content(html_body)
    text_message = sanitize_content(text_message)

    template = get_template("emails/wrapper.html")
    wrapper_context = get_wrapper_context(html_body)
    html_message = template.render(wrapper_context)

    send_mail_plus(
        subject,
        text_message,
        from_email,
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


def strip_tags_plus(text: str) -> str:
    """
    NOTE this renders unescaped user-data and should never used for display as HTML content

    copied and modified from https://bitbucket.org/maykinmedia/werkbezoek/src/develop/src/werkbezoek/utils/email.py
    """
    text = unwrap_anchors(text)
    text = django_strip_tags(text)
    lines = text.splitlines()
    transformed_lines = transform_lines(lines)
    deduplicated_newlines = deduplicate_newlines(transformed_lines)

    return "".join(deduplicated_newlines)


def transform_lines(lines: List[str]) -> List[str]:
    transformed_lines = []

    for line in lines:
        stripped_line = unescape(line)
        splitted_line = f"{' '.join(stripped_line.split())}".rstrip()

        transformed_lines.append(f"{splitted_line}\n")

    return transformed_lines


def deduplicate_newlines(lines: List[str]) -> List[str]:
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


def unwrap_anchors(html_str: str) -> str:
    """
    ugly util to append the href inside the anchor text so we can use strip-tags

    note this runs on un-trusted HTML content
    """
    if len(html_str) > MESSAGE_SIZE_LIMIT:
        raise SuspiciousOperation("email content-length exceeded safety limit")

    root = fromstring(html_str)

    for link in root.iterfind(".//a"):
        url = link.attrib.get("href", None)
        if not url:
            continue
        link.text += f" ({url})"

    return tostring(root, encoding="utf8").decode("utf8")


def get_confirmation_email_context_data(submission: "Submission") -> Dict[str, Any]:
    context = {
        # use private variables that can't be accessed in the template data, so that
        # template designers can't call the .delete method, for example. Variables
        # starting with underscores are blocked by the Django template engine.
        "_submission": submission,
        "_form": submission.form,  # should be the same as self.form
        **submission.data,
        "public_reference": submission.public_registration_reference,
        "form_name": submission.form.name,
    }

    # use the ``|date`` filter so that the timestamp is first localized to the correct
    # timezone, and then the date is formatted according to the django global setting.
    # This makes date representations consistent across the system.
    context["submission_date"] = date_filter(submission.completed_on)

    if submission.payment_required:
        context["payment_required"] = True
        context["payment_user_has_paid"] = submission.payment_user_has_paid
        context["payment_url"] = build_absolute_uri(
            reverse("payments:link", kwargs={"uuid": submission.uuid})
        )
        context["payment_price"] = str(submission.form.product.price)

    try:
        context["_appointment_id"] = submission.appointment_info.appointment_id
    except AppointmentInfo.DoesNotExist:
        pass

    return context


def render_confirmation_email_content(
    submission: "Submission", content: str, extra_context: Dict[str, Any] = None
):
    context = get_confirmation_email_context_data(submission)
    if extra_context:
        context.update(extra_context)

    rendered_content = Template(content).render(Context(context))

    return rendered_content
