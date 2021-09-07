from celery.contrib import rdb

from openforms.celery import app
from openforms.registrations.tasks import register_submission

from ..models import Submission

__all__ = ["register_submission", "obtain_submission_reference"]


@app.task(bind=True)
def obtain_submission_reference(task, submission_id: int) -> None:
    """
    Obtain a unique reference to be communicated to the end user.

    The reference is used in the payment, confirmation page and confirmation e-mail. It
    is possible that the backend registration failed or does not generate a reference
    (read: case number), in which case we need to generate a unique reference ourselves.
    """
    submission = Submission.objects.get(id=submission_id)

    # TODO: check the registration result if we can extract a reference from that,
    # otherwise generate one ourselves
    rdb.set_trace()
