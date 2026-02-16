from django.db import transaction

import structlog
from sqids import Sqids

from openforms.config.models import GlobalConfiguration

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

    with transaction.atomic():
        reference = generate_unique_submission_reference(submission)
        submission.public_registration_reference = reference
        submission.save(update_fields=["public_registration_reference"])

    return reference


def generate_unique_submission_reference(submission: Submission) -> str:
    """
    Generate unique reference based on the globally configured template.

    The random string part is generated from the submission pk with
    the alphabet which is uniquely shuffled for each OF instance.
    """
    config = GlobalConfiguration.get_solo()
    template: str = config.public_reference_template
    alphabet = config.public_reference_alphabet

    sqids = Sqids(min_length=6, alphabet=alphabet)
    uid = sqids.encode([submission.pk])

    return template.replace(
        "{year}",
        str(submission.created_on.year),
    ).replace("{uid}", uid)
