import logging

from celery_once import QueueOnce

from openforms.appointments.service import (
    AppointmentRegistrationFailed,
    AppointmentUpdateFailed,
    register_appointment,
)
from openforms.celery import app

from ..models import Submission

__all__ = [
    "maybe_register_appointment",
    "maybe_update_appointment",
]

logger = logging.getLogger(__name__)


def update_appointment(submission: Submission):
    # placeholder until real function is implemented
    # TODO: implement
    pass


@app.task(
    base=QueueOnce,
    ignore_result=False,
    once={"graceful": True},  # do not spam error monitoring
)
def maybe_register_appointment(submission_id: int) -> None:
    """
    Register an appointment for the submission IF relevant.

    If the submission is for a form which is configured to create appointments,
    ensure that the appointment is registered in the configured backend.

    This can either not be needed, be succesful or fail. Either way, the result should
    be stored in the database. If appointment registration fails, this feedback
    should find its way back to the end-user.
    """
    logger.info("Registering appointment for submission %d (if needed!)", submission_id)
    submission = Submission.objects.get(id=submission_id)
    try:
        register_appointment(submission)
    except AppointmentRegistrationFailed as exc:
        logger.info(
            "Appoinment registration failed, aborting workflow.",
            exc_info=exc,
            extra={"submission": submission_id},
        )
        raise


@app.task(
    base=QueueOnce,
    ignore_result=False,
    once={"graceful": True},  # do not spam error monitoring
)
def maybe_update_appointment(submission_id: int) -> None:
    """
    Check the submission state and update the appointment with the internal reference.

    The reference may be sourced from the registration backend, or it may be sourced
    internally because of problems with the registration backend. Either way,
    the appointment and submission must agree on the internal reference.

    This task should be scheduled after the submission backend registration was
    attempted and after the "final" reference was obtained.
    """
    submission = Submission.objects.get(id=submission_id)
    is_retrying = submission.needs_on_completion_retry
    logger.info("Updating appointment for submission %d (if needed!)", submission_id)
    try:
        update_appointment(submission)
    except AppointmentUpdateFailed:
        # if we're in the retry workflow, tasks must hard-fail to keep the retry flag
        # on.
        if is_retrying:
            raise
        submission.needs_on_completion_retry = True
        submission.save(update_fields=["needs_on_completion_retry"])
        return
