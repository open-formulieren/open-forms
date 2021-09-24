from openforms.celery import app
from openforms.logging import logevent

from ..models import Submission
from ..utils import send_confirmation_email

__all__ = ["maybe_send_confirmation_email"]


@app.task(bind=True, ignore_result=True)
def maybe_send_confirmation_email(task, submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)

    logevent.confirmation_email_start(submission)

    if hasattr(submission.form, "confirmation_email_template"):
        try:
            send_confirmation_email(submission)
        except Exception as e:
            logevent.confirmation_email_failure(submission, e)
            raise
    else:
        logevent.confirmation_email_skip(submission)
