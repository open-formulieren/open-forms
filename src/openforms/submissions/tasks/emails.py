from django.conf import settings
from django.db import DatabaseError, transaction
from django.template.defaultfilters import date as date_filter
from django.utils import translation
from django.utils.translation import gettext_lazy as _

import structlog
from celery_once import QueueOnce

from openforms.celery import app
from openforms.config.models import GlobalConfiguration
from openforms.emails.constants import (
    X_OF_CONTENT_TYPE_HEADER,
    X_OF_CONTENT_UUID_HEADER,
    X_OF_EVENT_HEADER,
    EmailContentTypeChoices,
    EmailEventChoices,
)
from openforms.emails.utils import send_mail_html
from openforms.frontend import get_frontend_redirect_url
from openforms.logging import logevent
from openforms.registrations.tasks import update_registration_with_confirmation_email
from openforms.template import render_from_string

from ..models import Submission
from ..utils import send_confirmation_email as _send_confirmation_email

__all__ = [
    "schedule_emails",
    "send_email_cosigner",
]

logger = structlog.stdlib.get_logger(__name__)


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

    This also protects against race conditions in the case that payment and cosign are completed at the same time.
    """
    try:
        submission = (
            Submission.objects.select_related("form")
            .select_for_update(of=("self",), nowait=True)
            .get(id=submission_id)
        )
    except DatabaseError:
        # lock acquiry failing is not necessarily a problem, it likely means that the
        # coordination mechanism works as intended
        logger.debug(
            "lock_acquiry_failed",
            action="submissions.send_confirmation_email",
            submission_id=submission_id,
        )
        return

    if (
        not submission.confirmation_email_sent
        or (
            not submission.cosign_confirmation_email_sent
            and submission.cosign_state.is_signed
        )
        or (
            not submission.payment_complete_confirmation_email_sent
            and submission.payment_user_has_paid
        )
    ):
        _send_confirmation_email(submission)

        on_confirmation_email_sent.delay(submission.pk)


@app.task(ignore_result=True)
def send_email_cosigner(submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)

    with translation.override(submission.language_code):
        config = GlobalConfiguration.get_solo()
        cosign = submission.cosign_state

        if not cosign.is_required or not (recipient := cosign.email):
            logger.warning(
                "skip_cosign_email",
                submission_uuid=str(submission.uuid),
                action="submissions.send_email_cosigner",
                reason="no_cosign_email_found_in_form",
            )
            return

        # build up the form URL based on the configuration - if no URLs are used in
        # the template, then users go through the flow where they manually have to find
        # the form and enter the OF code. However, when clickable links in emails are
        # allowed, we can enable a bunch of shortcuts and include the necessary
        # parameters for that.
        has_cosign_init_link = config.cosign_request_template_has_link
        form_url = get_frontend_redirect_url(
            submission,
            action="cosign-init" if has_cosign_init_link else "",
            action_params=(
                {
                    "code": submission.public_registration_reference,
                }
                if has_cosign_init_link
                else None
            ),
        )
        content = render_from_string(
            config.cosign_request_template,
            {
                "code": submission.public_registration_reference,
                "form_name": submission.form.name,
                "form_url": form_url,
                # use the ``|date`` filter so that the timestamp is first localized to the correct
                # timezone, and then the date is formatted according to the django global setting.
                # This makes date representations consistent across the system.
                "submission_date": date_filter(submission.completed_on),
            },
        )

        try:
            send_mail_html(
                subject=_("Co-sign request for {form_name}").format(
                    form_name=submission.form.name
                ),
                html_body=content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                text_message=content,
                extra_headers={
                    "Content-Language": submission.language_code,
                    X_OF_CONTENT_TYPE_HEADER: EmailContentTypeChoices.submission,
                    X_OF_CONTENT_UUID_HEADER: str(submission.uuid),
                    X_OF_EVENT_HEADER: EmailEventChoices.cosign_request,
                },
            )
        except Exception:
            logevent.cosigner_email_queuing_failure(submission)
            raise

        submission.cosign_request_email_sent = True
        submission.save(update_fields=("cosign_request_email_sent",))

        logevent.cosigner_email_queuing_success(submission)


@app.task(
    base=QueueOnce,
    ignore_result=True,
    once={"graceful": True},
)
def schedule_emails(submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)

    if (
        submission.confirmation_email_sent
        and submission.cosign_request_email_sent
        and submission.cosign_confirmation_email_sent
        and submission.payment_complete_confirmation_email_sent
    ):
        return

    #
    # Figure out which email(s) should be sent
    #

    if submission.cosign_state.is_waiting and not submission.cosign_request_email_sent:
        send_email_cosigner.delay(submission_id)

    if not submission.form.send_confirmation_email:
        logger.debug(
            "confirmation_email_skip",
            submission_uuid=str(submission.uuid),
            form_uuid=str(submission.form.uuid),
            reason="form_configured_no_confirmation_email",
        )
        logevent.confirmation_email_skip(submission)
        return

    execution_options = {}
    if not submission.confirmation_email_sent:
        # The confirmation email is sent after the user has submitted a form. It contains the generated PDF report
        # with information about whether payment/cosign is (still) needed or not. This is scheduled with a (15 min) countdown
        # if a payment is needed
        if submission.payment_required and not submission.payment_user_has_paid:
            # wait a while and check again
            execution_options["countdown"] = settings.PAYMENT_CONFIRMATION_EMAIL_TIMEOUT

    send_confirmation_email.apply_async(
        args=(submission.pk,),
        **execution_options,
    )
    logevent.confirmation_email_scheduled(
        submission, scheduling_options=execution_options
    )


@app.task(
    base=QueueOnce,
    ignore_result=True,
    once={"graceful": True},
)
def on_confirmation_email_sent(submission_id: int) -> None:
    """Hook that is called after the send confirmation email task has completed."""

    update_registration_with_confirmation_email(submission_id)
