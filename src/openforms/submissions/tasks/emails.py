from openforms.celery import app

from ..models import Submission
from ..utils import send_confirmation_email

__all__ = ["maybe_send_confirmation_email"]


@app.task(bind=True)
def maybe_send_confirmation_email(task, submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)
    if hasattr(submission.form, "confirmation_email_template"):
        send_confirmation_email(submission)
