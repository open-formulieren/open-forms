import logging

from django.conf import settings
from django.db import DatabaseError, transaction
from django.template.loader import get_template
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from celery_once import QueueOnce

from openforms.celery import app
from openforms.config.models import GlobalConfiguration
from openforms.emails.utils import send_mail_html
from openforms.logging import logevent

from ..models import Submission
from ..utils import send_confirmation_email as _send_confirmation_email

__all__ = [
    "schedule_emails",
    "send_email_cosigner",
]


logger = logging.getLogger(__name__)


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
            .select_for_update(nowait=True)
            .get(id=submission_id)
        )
    except DatabaseError:
        logger.debug(
            "Submission %d confirmation e-mail task failed to acquire a lock. This is "
            "likely intended behaviour to prevent race conditions.",
            submission_id,
        )
        return

    if (
        not submission.confirmation_email_sent
        or (
            not submission.cosign_confirmation_email_sent and submission.cosign_complete
        )
        or (
            not submission.payment_complete_confirmation_email_sent
            and submission.payment_user_has_paid
        )
    ):
        _send_confirmation_email(submission)


@app.task()
def send_email_cosigner(submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)

    with translation.override(submission.language_code):
        config = GlobalConfiguration.get_solo()

        if not (recipient := submission.cosigner_email):
            logger.warning(
                "No co-signer email found in the form. Skipping co-sign email for submission %d.",
                submission.id,
            )
            return

        template = get_template("emails/cosign.html")
        content = template.render(
            {
                "code": submission.public_registration_reference,
                "form_name": submission.form.name,
                "form_url": submission.cleaned_form_url,
                "show_form_link": config.show_form_link_in_cosign_email,
            }
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

    if submission.waiting_on_cosign and not submission.cosign_request_email_sent:
        send_email_cosigner.delay(submission_id)

    if not submission.form.send_confirmation_email:
        logger.debug(
            "Form %d is configured to not send a confirmation email for submission %d, "
            "skipping the confirmation e-mail.",
            submission.form.id,
            submission.id,
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
        args=(submission.id,),
        **execution_options,
    )
    logevent.confirmation_email_scheduled(
        submission, scheduling_options=execution_options
    )
