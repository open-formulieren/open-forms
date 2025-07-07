import re
from collections.abc import Sequence
from typing import Any
from urllib.parse import urlsplit

from django.conf import settings
from django.template.loader import get_template

from mail_cleaner.mail import send_mail_plus
from mail_cleaner.sanitizer import sanitize_content as _sanitize_content
from mail_cleaner.text import strip_tags_plus

from openforms.config.models import GlobalConfiguration, Theme
from openforms.template import openforms_backend, render_from_string

from .context import get_wrapper_context

MESSAGE_SIZE_LIMIT = 2 * 1024 * 1024

RE_NON_WHITESPACE = re.compile(r"\S")


def get_system_netloc_allowlist() -> list[str]:
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
    return _sanitize_content(content, allowlist)


AttachmentsType = Sequence[tuple[str, str, Any]] | None


def send_mail_html(
    subject: str,
    html_body: str,
    from_email: str,
    recipient_list: list[str],
    cc: list[str] | None = None,
    attachment_tuples: AttachmentsType = None,
    fail_silently: bool = False,
    text_message: str | None = None,
    extra_headers: dict[str, str] | None = None,
    theme: Theme | None = None,
) -> None:
    """
    Send outoing email with HTML content, wrapped in our scaffolding.

    If no explicit text variant if supplied, it will be generated best-effort by
    :func:`strip_tags_plus`.
    """
    # render versions
    if not text_message:
        text_message = strip_tags_plus(html_body)

    # sanitize
    html_body = sanitize_content(html_body)
    text_message = sanitize_content(text_message)

    template = get_template("emails/wrapper.html")
    wrapper_context = get_wrapper_context(html_body, theme=theme)
    html_message = template.render(wrapper_context)

    send_mail_plus(
        subject,
        text_message,
        from_email,
        recipient_list,
        cc=cc,
        html_message=html_message,
        fail_silently=fail_silently,
        attachments=attachment_tuples,
        headers=extra_headers,
    )


def render_email_template(
    template: str, context: dict, disable_autoescape: bool = False, **extra_context: Any
) -> str:
    render_context = {**context, **extra_context}
    return render_from_string(
        template,
        render_context,
        backend=openforms_backend,
        disable_autoescape=disable_autoescape,
    )
