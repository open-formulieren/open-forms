import traceback

import structlog
from celery_once import QueueOnce

from openforms.celery import app
from openforms.config.models import GlobalConfiguration
from openforms.logging import audit_logger
from openforms.submissions.constants import PostSubmissionEvents, RegistrationStatuses
from openforms.submissions.models import Submission

from .services import update_submission_payment_registration

__all__ = ["update_submission_payment_status"]


logger = structlog.stdlib.get_logger(__name__)


@app.task(
    base=QueueOnce,
    once={"graceful": True},  # do not spam error monitoring
)
def update_submission_payment_status(
    submission_id: int, event: PostSubmissionEvents
) -> None:
    log = logger.bind(
        action="payments.update_payment_status",
        submission_id=submission_id,
        triggered_by=event,
    )
    log.info("update_payment_status_task_received")
    submission = Submission.objects.select_related("auth_info").get(id=submission_id)
    log = log.bind(
        submission_uuid=str(submission.uuid),
        payment_required=submission.payment_required,
    )
    audit_log = audit_logger.bind(**structlog.get_context(log))
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
        audit_log.info(
            "registration_payment_update_skip",
            wait_for_payment_to_register=config.wait_for_payment_to_register,
            registration_status=submission.registration_status,
            payment_registered=submission.payment_registered,
            registration_attempts=submission.registration_attempts,
            max_number_of_attempts=config.registration_attempt_limit,
        )
        return

    try:
        update_submission_payment_registration(submission)
    except Exception as exc:
        log.info("payment_registration_update_failure", exc_info=exc)
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
