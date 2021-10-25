import logging

from celery_once import QueueOnce

from openforms.celery import app
from openforms.submissions.models import Submission

from .services import update_submission_payment_registration

__all__ = ["update_submission_payment_status"]

logger = logging.getLogger(__name__)


@app.task(
    base=QueueOnce,
    ignore_result=True,
    once={"graceful": True},  # do not spam error monitoring
)
def update_submission_payment_status(submission_id: int):
    logger.info(
        "Updating payment information for submission %d (if needed!)", submission_id
    )
    submission = Submission.objects.get(id=submission_id)
    try:
        update_submission_payment_registration(submission)
    except Exception as exc:
        logger.info("Updating submission payment registration failed", exc_info=exc)
        submission.needs_on_completion_retry = True
        submission.save(update_fields=["needs_on_completion_retry"])
        return
