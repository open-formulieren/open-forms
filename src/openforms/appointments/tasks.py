import logging
import warnings

from celery_once import QueueOnce

from openforms.celery import app
from openforms.submissions.models import Submission

from .core import book_for_submission
from .exceptions import AppointmentRegistrationFailed, NoAppointmentForm
from .models import AppointmentInfo
from .utils import book_appointment_for_submission

__all__ = ["maybe_register_appointment"]

logger = logging.getLogger(__name__)


@app.task(
    base=QueueOnce,
    ignore_result=False,
    once={"graceful": True},  # do not spam error monitoring
)
def maybe_register_appointment(submission_id: int) -> None | str:
    """
    Register an appointment for the submission IF relevant.

    If the submission is for a form which is configured to create appointments,
    ensure that the appointment is registered in the configured backend.

    This can either not be needed, be successful or fail. Either way, the result should
    be stored in the database. If appointment registration fails, this feedback
    should find its way back to the end-user.
    """
    warnings.warn(
        "This task is deprecated because of the new appointment flow.",
        PendingDeprecationWarning,
    )
    logger.info("Registering appointment for submission %d (if needed!)", submission_id)
    submission = Submission.objects.select_related("form").get(id=submission_id)

    try:
        appointment_id = submission.appointment_info.appointment_id
    except AppointmentInfo.DoesNotExist:
        pass
    else:
        # idempotency - do not register a new appointment if there already is one.
        if appointment_id:
            logger.info(
                "Submission %s already has an appointment ID, aborting.", submission.pk
            )
            return

    # Try the new appointments implementation first
    try:
        return book_for_submission(submission=submission)
    except NoAppointmentForm:
        pass
    except AppointmentRegistrationFailed as exc:
        logger.info(
            "Appointment registration failed, aborting workflow.",
            exc_info=exc,
            extra={"submission": submission_id},
        )
        raise

    # otherwise, fall back to the old form
    logger.info("Attempting old appointment booking for submission %r", submission_id)
    try:
        book_appointment_for_submission(submission)
    except AppointmentRegistrationFailed as exc:
        logger.info(
            "Appointment registration failed, aborting workflow.",
            exc_info=exc,
            extra={"submission": submission_id},
        )
        raise
