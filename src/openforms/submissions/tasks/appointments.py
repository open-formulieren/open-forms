import logging

from celery_once import QueueOnce

from openforms.appointments.service import (
    AppointmentRegistrationFailed,
    register_appointment,
)
from openforms.celery import app

from ..models import Submission

__all__ = ["maybe_register_appointment"]

logger = logging.getLogger(__name__)


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
