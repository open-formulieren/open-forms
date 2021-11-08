import html
import logging
from typing import Any

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.core.exceptions import ObjectDoesNotExist

from openforms.config.models import GlobalConfiguration
from openforms.emails.utils import send_mail_html, strip_tags_plus
from openforms.logging import logevent

from .constants import SUBMISSIONS_SESSION_KEY, UPLOADS_SESSION_KEY
from .models import Submission, TemporaryFileUpload

logger = logging.getLogger(__name__)


def append_to_session_list(session: SessionBase, session_key: str, value: Any) -> None:
    # note: possible race condition with concurrent requests
    active = session.get(session_key, [])
    if value not in active:
        active.append(value)
        session[session_key] = active


def remove_from_session_list(
    session: SessionBase, session_key: str, value: Any
) -> None:
    # note: possible race condition with concurrent requests
    active = session.get(session_key, [])
    if value in active:
        active.remove(value)
        session[session_key] = active


def add_submmission_to_session(submission: Submission, session: SessionBase) -> None:
    """
    Store the submission UUID in the request session for authorization checks.
    """
    append_to_session_list(session, SUBMISSIONS_SESSION_KEY, str(submission.uuid))


def remove_submission_from_session(
    submission: Submission, session: SessionBase
) -> None:
    """
    Remove the submission UUID from the session if it's present.
    """
    remove_from_session_list(session, SUBMISSIONS_SESSION_KEY, str(submission.uuid))


def add_upload_to_session(upload: TemporaryFileUpload, session: SessionBase) -> None:
    """
    Store the upload UUID in the request session for authorization checks.
    """
    append_to_session_list(session, UPLOADS_SESSION_KEY, str(upload.uuid))


def remove_upload_from_session(
    upload: TemporaryFileUpload, session: SessionBase
) -> None:
    """
    Remove the submission UUID from the session if it's present.
    """
    remove_from_session_list(session, UPLOADS_SESSION_KEY, str(upload.uuid))


def remove_submission_uploads_from_session(
    submission: Submission, session: SessionBase
) -> None:
    for attachment in submission.get_attachments().filter(temporary_file__isnull=False):
        remove_upload_from_session(attachment.temporary_file, session)


def send_confirmation_email(submission: Submission):
    to_emails = submission.get_email_confirmation_recipients(submission.data)
    if not to_emails:
        logger.warning(
            "Could not determine the recipient e-mail address for submission %d, "
            "skipping the confirmation e-mail.",
            submission.id,
        )
        logevent.confirmation_email_skip(submission)
        return

    try:
        if not submission.form.send_custom_confirmation_email:
            # Raise our own attribute error so the global confirmation email is sent
            raise AttributeError("Form should not send it's own confirmation email")
        email_template = submission.form.confirmation_email_template
        subject = email_template.subject
        html_content = email_template.render(submission)
        text_content = email_template.render(submission, {"rendering_text": True})
    except (AttributeError, ObjectDoesNotExist):
        config = GlobalConfiguration.get_solo()
        subject = config.confirmation_email_subject
        html_content = config.render_confirmation_email_content(submission)
        text_content = config.render_confirmation_email_content(
            submission, {"rendering_text": True}
        )

    # post process since the mail template has html markup and django escaped entities
    text_content = strip_tags_plus(text_content)
    text_content = html.unescape(text_content)

    send_mail_html(
        subject,
        html_content,
        settings.DEFAULT_FROM_EMAIL,  # TODO: add config option to specify sender e-mail
        to_emails,
        fail_silently=False,
        text_message=text_content,
    )

    submission.confirmation_email_sent = True
    submission.save(update_fields=("confirmation_email_sent",))

    logevent.confirmation_email_success(submission)
