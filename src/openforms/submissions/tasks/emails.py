from django.conf import settings

from openforms.celery import app
from openforms.logging import logevent

from ..models import Submission
from ..utils import send_confirmation_email

__all__ = ["maybe_send_confirmation_email"]


@app.task(bind=True, ignore_result=True)
def maybe_send_confirmation_email(task, submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)
    if not hasattr(submission.form, "confirmation_email_template"):
        logevent.confirmation_email_skip(submission)
        return
    if submission.confirmation_email_sent:
        return

    if submission.payment_required and not submission.payment_user_has_paid:
        # wait a while and check again
        send_confirmation_email_after_payment_timeout.apply_async(
            args=(submission.id,), countdown=settings.PAYMENT_CONFIRMATION_EMAIL_TIMEOUT
        )
    else:
        logevent.confirmation_email_start(submission)
        try:
            send_confirmation_email(submission)
        except Exception as e:
            logevent.confirmation_email_failure(submission, e)
            raise


@app.task(bind=True, ignore_result=True)
def send_confirmation_email_after_payment_timeout(task, submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)
    if submission.confirmation_email_sent:
        return

    logevent.confirmation_email_start(submission)
    try:
        send_confirmation_email(submission)
    except Exception as e:
        logevent.confirmation_email_failure(submission, e)
        raise
