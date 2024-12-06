import logging

from celery_once import QueueOnce

from openforms.celery import app
from openforms.submissions.models import Submission

from .core import book_for_submission
from .exceptions import AppointmentRegistrationFailed, NoAppointmentForm

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

    This can either be successful or fail. Either way, the result should
    be stored in the database. If appointment registration fails, this feedback
    should find its way back to the end-user.
    """
    logger.info("Registering appointment for submission %d", submission_id)
    submission = Submission.objects.select_related("form").get(id=submission_id)

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
