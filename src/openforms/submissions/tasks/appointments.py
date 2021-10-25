import logging

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


class AppointmentRegistrationAborted(Exception):
    pass


@app.task()
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
            "Appoinment registration failed. The should_retry flag is set to: %r",
            exc.should_retry,
        )
        # some user-error that can't be retried automatically, we _fail_ the task here
        # to signal that downstream processing should not proceed.
        if not exc.should_retry:
            raise AppointmentRegistrationAborted(
                "Could not register appointment"
            ) from exc

        else:
            submission.needs_on_completion_retry = True
            submission.save(update_fields=["needs_on_completion_retry"])
            # the registration flow can signal that registration failed, but that should not
            # hold up the entire parent chain (completion or completion_retry).
            return


@app.task()
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
    logger.info("Updating appointment for submission %d (if needed!)", submission_id)
    try:
        update_appointment(submission)
    except AppointmentUpdateFailed:
        submission.needs_on_completion_retry = True
        submission.save(update_fields=["needs_on_completion_retry"])
        return
