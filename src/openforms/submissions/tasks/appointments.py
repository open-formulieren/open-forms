import logging

from openforms.appointments.service import (
    AppointmentRegistrationFailed,
    register_appointment,
)
from openforms.celery import app

from ..models import Submission
from .utils import maybe_retry_in_workflow

__all__ = [
    "maybe_register_appointment",
    "maybe_update_appointment",
]

logger = logging.getLogger(__name__)


TIMEOUT = 10  # in seconds


class AppointmentRegistrationAborted(Exception):
    pass


def should_retry_appointment_registration(exception, task) -> bool:
    if not exception.should_retry:
        raise AppointmentRegistrationAborted(
            "Could not register appointment"
        ) from exception
    return True


@maybe_retry_in_workflow(
    retry_backoff=True,
    timeout=10,
    retry_for=(AppointmentRegistrationFailed,),
    should_retry=should_retry_appointment_registration,
)
@app.task(bind=True, max_retries=3)
def maybe_register_appointment(task, submission_id: int) -> None:
    """
    Register an appointment for the submission IF relevant.

    If the submission is for a form which is configured to create appointments,
    ensure that the appointment is registered in the configured backend.

    This can either not be needed, be succesful or fail. Either way, the result should
    be stored in the database. If appointment registration fails, this feedback
    should find its way back to the end-user.
    """
    logger.info("Registering appointment for submission %d", submission_id)
    submission = Submission.objects.get(id=submission_id)
    register_appointment(submission)


@app.task(bind=True)
def maybe_update_appointment(task, submission_id: int) -> None:
    """
    Check the submission state and update the appointment with the internal reference.

    The reference may be sourced from the registration backend, or it may be sourced
    internally because of problems with the registration backend. Either way,
    the appointment and submission must agree on the internal reference.

    This task should be scheduled after the submission backend registration was
    attempted and after the "final" reference was obtained.
    """
    submission = Submission.objects.get(id=submission_id)
    logger.info("Updating appointment for submission %d", submission_id)
    pass  # TODO: implement!
