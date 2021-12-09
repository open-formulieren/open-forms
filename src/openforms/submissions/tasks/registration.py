import logging

from django.db import IntegrityError, transaction
from django.utils.crypto import get_random_string

from openforms.celery import app
from openforms.registrations.tasks import register_submission

from ..models import Submission

__all__ = [
    "register_submission",
    "obtain_submission_reference",
    "set_submission_reference",
]

logger = logging.getLogger(__name__)


@app.task
@transaction.atomic
def obtain_submission_reference(submission_id: int) -> str:
    """
    Task wrapper for set_submission_reference()
    """
    submission = Submission.objects.get(id=submission_id)
    set_submission_reference(submission)


def set_submission_reference(submission: Submission) -> str:
    """
    Obtain a unique reference to be communicated to the end user.

    The reference is used in the payment, confirmation page and confirmation e-mail. It
    is possible that the backend registration failed or does not generate a reference
    (read: case number), in which case we need to generate a unique reference ourselves.
    """
    # idempotency - do not run this again if there already is a reference!
    if submission.public_registration_reference:
        logger.info(
            "Submission %d already had a public registration reference, aborting.",
            submission.id,
        )
        return

    # race-condition detection. There's no reason/logic after the number 5 other than
    # gut feeling.
    MAX_NUM_ATTEMPTS = 5
    race_condition_suspected, save_attempts = False, 0

    while (
        race_condition_suspected or save_attempts == 0
    ) and save_attempts < MAX_NUM_ATTEMPTS:
        try:
            with transaction.atomic():
                reference = get_reference_for_submission(submission)
                submission.public_registration_reference = reference
                submission.save(update_fields=["public_registration_reference"])
        except IntegrityError as error:
            race_condition_suspected = True
            logger.warning(
                "Likely race condition being handled for submission %d, did %d save attempts.",
                submission.id,
                save_attempts + 1,
                exc_info=error,
            )
            save_attempts += 1
            # if we're about to leave the loop, re-raise the original exception
            if save_attempts >= MAX_NUM_ATTEMPTS:
                raise
        else:
            return reference
    # should never reach this
    raise RuntimeError(  # noqa
        "Unexpected code-path! Either the reference should have been saved successfully, "
        "or the error should have been re-raised."
    )


def get_reference_for_submission(submission: Submission) -> str:
    # Circular import
    from openforms.registrations.service import (
        NoSubmissionReference,
        extract_submission_reference,
    )

    try:
        reference = extract_submission_reference(submission)
    except NoSubmissionReference as exc:
        logger.info(
            "Could not get the reference from the registration result for submission %d, "
            "generating one instead",
            submission.id,
            exc_info=exc,
        )
        reference = generate_unique_submission_reference()
    return reference


def get_random_reference() -> str:
    # 32 characters with length 6 -> 32^6 possible combinations.
    # that's roughly one billion combinations before we run out of options.
    # Also note that submissions are pruned after a (configurable) number of days, so
    # used references do become available again after that time.
    # TODO: maybe include date param?
    random_string = get_random_string(
        length=6, allowed_chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
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
