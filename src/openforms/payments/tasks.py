import logging
import traceback

from celery_once import QueueOnce

from openforms.celery import app
from openforms.config.models import GlobalConfiguration
from openforms.logging import logevent
from openforms.submissions.constants import PostSubmissionEvents, RegistrationStatuses
from openforms.submissions.models import Submission

from .services import update_submission_payment_registration

__all__ = ["update_submission_payment_status"]


logger = logging.getLogger(__name__)


@app.task(
    base=QueueOnce,
    once={"graceful": True},  # do not spam error monitoring
)
def update_submission_payment_status(
    submission_id: int, event: PostSubmissionEvents
) -> None:
    logger.info(
        "Updating payment information for submission %d (if needed!)", submission_id
    )
    submission = Submission.objects.select_related("auth_info").get(id=submission_id)
    config = GlobalConfiguration.get_solo()

    should_skip = config.wait_for_payment_to_register or any(
        (
            submission.registration_status != RegistrationStatuses.success,
            not submission.payment_required,
            submission.payment_registered,
            submission.registration_attempts >= config.registration_attempt_limit,
        )
    )
    if should_skip:
        logevent.registration_payment_update_skip(submission)
        logger.info("Skipping payment update for submission %d.", submission_id)
        return

    try:
        update_submission_payment_registration(submission)
    except Exception as exc:
        logger.info("Updating submission payment registration failed", exc_info=exc)
        submission.needs_on_completion_retry = True
        submission.registration_result = {
            **(submission.registration_result or {}),
            **{"payment_status_update_traceback": traceback.format_exc()},
        }
        submission.save(
            update_fields=["needs_on_completion_retry", "registration_result"]
        )
        if event == PostSubmissionEvents.on_retry:
            raise exc
        return
