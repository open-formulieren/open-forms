import logging

from django.db import transaction
from django.utils.crypto import get_random_string

from openforms.celery import app
from openforms.registrations.tasks import register_submission

from ..models import Submission

__all__ = ["register_submission", "obtain_submission_reference"]

logger = logging.getLogger(__name__)


@app.task
@transaction.atomic
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
    # idempotency - do not run this again if there already is a reference!
    if submission.public_registration_reference:
        logger.info(
            "Submission %d already had a public registration reference, aborting.",
            submission_id,
        )
        return

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


def get_random_reference() -> str:
    # 36 characters with length 6 -> 36^6 possible combinations.
    # that's roughly 2.1 billion combinations before we run out of options.
    # Also note that submissions are pruned after a (configurable) number of days, so
    # used references do become available again after that time.
    random_string = get_random_string(
        length=6, allowed_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    )
    return f"OF-{random_string}"


def generate_unique_submission_reference() -> str:
    """
    Generate a random but unique reference.
    """
    MAX_ATTEMPTS = 100  # ensure we have finite loops (while is evil)
    iterations = 0

    for _ in range(MAX_ATTEMPTS):
        iterations += 1
        reference = get_random_reference()
        exists = Submission.objects.filter(
            public_registration_reference=reference
        ).exists()
        if exists is False:
            return reference

    # loop ran all the way to the end without finding unused reference
    # (otherwise it would have returned)
    raise RuntimeError(f"Could not get a unused reference after {iterations} attempts!")
