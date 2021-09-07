import logging

from openforms.celery import app
from openforms.registrations.tasks import register_submission

from ..models import Submission

__all__ = ["register_submission", "obtain_submission_reference"]

logger = logging.getLogger(__name__)


@app.task
def obtain_submission_reference(submission_id: int) -> str:
    """
    Obtain a unique reference to be communicated to the end user.

    The reference is used in the payment, confirmation page and confirmation e-mail. It
    is possible that the backend registration failed or does not generate a reference
    (read: case number), in which case we need to generate a unique reference ourselves.
    """
    # circular import dependency
    from openforms.registrations.service import (
        NoSubmissionReference,
        extract_submission_reference,
    )

    submission = Submission.objects.get(id=submission_id)
    try:
        reference = extract_submission_reference(submission)
    except NoSubmissionReference as exc:
        logger.info(
            "Could not get the reference from the registration result for submission %d, "
            "generating one instead",
            submission_id,
            exc_info=exc,
        )
        reference = generate_unique_submission_reference()

    submission.public_registration_reference = reference
    submission.save(update_fields=["public_registration_reference"])
    return reference


def generate_unique_submission_reference() -> str:
    raise NotImplementedError("TODO")
