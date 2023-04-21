import logging

from django.conf import settings
from django.db import DatabaseError, transaction
from django.utils import translation

from celery_once import QueueOnce
from mail_cleaner.text import strip_tags_plus

from openforms.appointments.utils import get_confirmation_mail_suffix
from openforms.celery import app
from openforms.emails.confirmation_emails import get_confirmation_email_context_data
from openforms.emails.utils import render_email_template, send_mail_html
from openforms.logging import logevent

from ..models import Submission
from ..utils import send_confirmation_email as _send_confirmation_email

__all__ = [
    "maybe_send_confirmation_email",
    "send_confirmation_email",
    "send_cosign_confirmation_email",
]

logger = logging.getLogger(__name__)


@app.task(
    base=QueueOnce,
    ignore_result=True,
    once={"graceful": True},
)
def maybe_send_confirmation_email(submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)
    if submission.confirmation_email_sent:
        return

    execution_options = {}

    # if the form requires payment and the user has not paid yet, stall for a maximum
    # of ``settings.PAYMENT_CONFIRMATION_EMAIL_TIMEOUT``. If the payment arrives inside
    # of this window, another task instance will be triggered and the e-mail will be
    # sent out "immediately". The queued future task will then exit early because of the
    # idempotency checks.
    if submission.payment_required and not submission.payment_user_has_paid:
        # wait a while and check again
        execution_options["countdown"] = settings.PAYMENT_CONFIRMATION_EMAIL_TIMEOUT

    # schedule the actual sending task
    send_confirmation_email.apply_async(
        args=(submission.id,),
        **execution_options,
    )


@app.task(ignore_result=True)
@transaction.atomic()
def send_confirmation_email(submission_id: int) -> None:
    """
    Render and send the confirmation e-mail if conditions are met.

    The following conditions must apply before an e-mail can be sent:

    1. There may not have been an e-mail sent out yet
    2. There must be a template configured

    Note that this task is NOT a celery-once task - only the function arguments are
    taken into account for the lock-key and not the countdown/eta. This would break
    the mechanism where the task is scheduled with the timeout of 15 minutes from
    :func:`maybe_send_confirmation_email` already, followed by the payment views
    calling this task for immediate execution. The immediate execution would then not
    be scheduled and we would always get the timeout e-mail.

    We protect against race-conditions by locking the submission database row, if a
    lock can not be acquired, this means that another transaction already holds the lock
    and is sending an e-mail, so we abort our own attempt.
    """
    try:
        submission = Submission.objects.select_for_update(nowait=True).get(
            id=submission_id
        )
    except DatabaseError:
        logger.debug(
            "Submission %d confirmation e-mail task failed to acquire a lock. This is "
            "likely intended behaviour to prevent race conditions.",
            submission_id,
        )
        return

    if submission.confirmation_email_sent:
        return

    _send_confirmation_email(submission)


@app.task()
def send_cosign_confirmation_email(submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)

    # TODO logs

    # TODO templates
    subject_template, content_template = (
        "The form {{ form_name }} was co-signed.",
        "Dear, the form {{ form_name }} was co-signed and has been processed.",
    )

    to_emails = submission.get_email_confirmation_recipients(submission.data)
    context = get_confirmation_email_context_data(submission)

    if to_emails:
        # render the templates with the submission context
        with translation.override(submission.language_code):
            subject = render_email_template(
                subject_template, context, rendering_text=True, disable_autoescape=True
            ).strip()

            if subject_suffix := get_confirmation_mail_suffix(submission):
                subject = f"{subject} {subject_suffix}"

            html_content = render_email_template(content_template, context)
            text_content = strip_tags_plus(
                render_email_template(content_template, context, rendering_text=True),
                keep_leading_whitespace=True,
            )

            try:
                send_mail_html(
                    subject,
                    html_content,
                    settings.DEFAULT_FROM_EMAIL,  # TODO: add config option to specify sender e-mail
                    to_emails,
                    text_message=text_content,
                )
            except Exception as e:
                logevent.confirmation_email_failure(submission, e)
                logger.error("Couldn't send the confirmation email after co-sign")
    else:
        logger.warning(
            "Could not determine the recipient e-mail address for submission %d, "
            "skipping the confirmation e-mail.",
            submission.id,
        )
        logevent.confirmation_email_skip(submission)

    co_signer_email = submission.get_cosigner_email()

    subject_template, content_template = (
        "You co-signed {{ form_name }}",
        "Dear, thank you for co-signing the form {{ form_name }}. The form has been processed.",
    )

    subject = render_email_template(
        subject_template, context, rendering_text=True, disable_autoescape=True
    ).strip()
    html_content = render_email_template(content_template, context)
    text_content = strip_tags_plus(
        render_email_template(content_template, context, rendering_text=True),
        keep_leading_whitespace=True,
    )

    try:
        send_mail_html(
            subject,
            html_content,
            settings.DEFAULT_FROM_EMAIL,  # TODO: add config option to specify sender e-mail
            [co_signer_email],
            text_message=text_content,
        )
    except Exception:
        logger.error("Couldn't send the confirmation email to the co-signer.")
        raise
