from django.db import IntegrityError, transaction

import structlog
from sqids import Sqids

from ..config.models import GlobalConfiguration
from .models import Submission

logger = structlog.stdlib.get_logger(__name__)


def set_submission_reference(submission: Submission) -> str | None:
    """
    Obtain a unique reference to be communicated to the end user.

    The reference is used in the payment, confirmation page and confirmation e-mail. It
    is possible that the backend registration failed or does not generate a reference
    (read: case number), in which case we need to generate a unique reference ourselves.
    """
    log = logger.bind(
        action="submissions.set_submission_reference",
        submission_uuid=str(submission.uuid),
    )

    # idempotency - do not run this again if there already is a reference!
    if submission.public_registration_reference:
        log.info("skip_set_public_reference", reason="reference_already_set")
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
                reference = generate_unique_submission_reference(submission)
                submission.public_registration_reference = reference
                submission.save(update_fields=["public_registration_reference"])
        except IntegrityError as error:
            race_condition_suspected = True
            save_attempts += 1
            log.warning(
                "likely_race_condition_detected",
                num_attempts_done=save_attempts,
                exc_info=error,
            )
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


def generate_unique_submission_reference(submission: Submission) -> str:
    """
    Generate unique reference based on the globally configured template.

    The random string part is generated from the submission pk with
    the alphabet which is uniquely shuffled for each OF instance.
    """
    config = GlobalConfiguration.get_solo()
    template: str = config.public_reference_template
    alphabet = config.public_reference_alphabet

    # 32 characters with length 6 -> 32^6 possible combinations.
    # that's roughly one billion combinations before we run out of options.
    # Also note that submissions are pruned after a (configurable) number of days, so
    # used references do become available again after that time.
    sqids = Sqids(min_length=6, alphabet=alphabet)
    uid = sqids.encode([submission.pk])

    return template.replace("{year}", str(submission.created_on.year)).replace(
        "{uid}", uid
    )
