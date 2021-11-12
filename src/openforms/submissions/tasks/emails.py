import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError, transaction

from celery_once import QueueOnce

from openforms.celery import app
from openforms.logging import logevent

from ..models import Submission
from ..utils import send_confirmation_email as _send_confirmation_email

__all__ = ["maybe_send_confirmation_email"]

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

    try:
        # access the reverse of the one2one
        submission.form.confirmation_email_template
    except (AttributeError, ObjectDoesNotExist):
        logevent.confirmation_email_skip(submission)
        return

    logevent.confirmation_email_start(submission)
    try:
        _send_confirmation_email(submission)
    except Exception as e:
        logevent.confirmation_email_failure(submission, e)
        raise
