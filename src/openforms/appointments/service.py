"""
Public Python API to interact with the appointments module.

The public exports in this module can be called by other apps in this project.
Implementation details remain private to the appointments app and should not be used
outside of this app.
"""
import logging

from openforms.submissions.models import Submission

from .exceptions import AppointmentRegistrationFailed, AppointmentUpdateFailed
from .models import AppointmentInfo
from .utils import get_confirmation_mail_suffix

logger = logging.getLogger(__name__)

__all__ = [
    "AppointmentRegistrationFailed",
    "AppointmentUpdateFailed",
    "register_appointment",
    "get_confirmation_mail_suffix",
]


def register_appointment(submission: Submission) -> None:
    """
    Register an appointment for a given submission, if needed.

    This function must be idempotent, since it's called in a celery task. This function
    is responsible for updating all the state information in the database, such as
    tracking the appointment ID _if_ relevant. If no appointment should be registered
    because the submission form is not an appointment form, then this function just
    returns.

    :param submission: :class:`Submission` instance containing all the relevant
      submission data.
    :raises AppointmentRegistrationFaild: if the submission form is an appointment form
      and registration was attempted. The state will already have been updated in the
      database with the relevant context/information - the exception just signals the
      failure to the caller so that it can retry if needed.
    """
    from .utils import book_appointment_for_submission

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

    book_appointment_for_submission(submission)
