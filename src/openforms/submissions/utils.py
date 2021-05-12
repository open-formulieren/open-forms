from smtplib import SMTP, SMTPServerDisconnected
from typing import Union

from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.http import HttpRequest
from django.utils.module_loading import import_string

from rest_framework.request import Request

from .constants import SUBMISSIONS_SESSION_KEY
from .models import SMTPServerConfig, Submission


def add_submmission_to_session(
    submission: Submission, request: Union[Request, HttpRequest]
) -> None:
    """
    Store the submission UUID in the request session for authorization checks.
    """
    # note: possible race condition with concurrent requests
    submissions = request.session.get(SUBMISSIONS_SESSION_KEY, [])
    submissions.append(str(submission.uuid))
    request.session[SUBMISSIONS_SESSION_KEY] = submissions


def remove_submission_from_session(
    submission: Submission, request: Union[Request, HttpRequest]
) -> None:
    """
    Remove the submission UUID from the session if it's present.
    """
    id_to_check = str(submission.uuid)
    submissions = request.session.get(SUBMISSIONS_SESSION_KEY, [])
    if id_to_check in submissions:
        submissions.remove(id_to_check)
        request.session[SUBMISSIONS_SESSION_KEY] = submissions


def send_confirmation_email(submission):
    email_template = submission.form.confirmation_email_template

    data = {}
    for step in submission.steps:
        data.update(step.data)

    smtp_config = SMTPServerConfig.get_solo()

    to_email = submission.form.get_email_recipient(data)
    content = email_template.render(data)

    send_mail(
        email_template.subject,
        content,
        smtp_config.default_from_email,
        [to_email],
        fail_silently=False,
        html_message=content,
    )


# Source: https://stackoverflow.com/a/14678470
def test_conn_open(smtp_config):
    try:
        conn = SMTP(f"{smtp_config.host}:{smtp_config.port}")
        status = conn.noop()[0]
    except (
        ConnectionRefusedError,
        SMTPServerDisconnected,
    ):  # smtplib.SMTPServerDisconnected
        status = -1
    return True if status == 250 else False
