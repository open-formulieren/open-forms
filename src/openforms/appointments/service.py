"""
Public Python API to interact with the appointments module.

The public exports in this module can be called by other apps in this project.
Implementation details remain private to the appointments app and should not be used
outside of this app.
"""
from openforms.submissions.models import Submission

__all__ = ["AppointmentRegistrationFailed", "register_appointment"]


class AppointmentRegistrationFailed(Exception):
    def __init__(self, *args, **kwargs):
        self.should_retry = kwargs.pop("should_retry", False)
        super().__init__(*args, **kwargs)


def register_appointment(submission: Submission) -> None:
    """
    Register an appointment for a given submission, if needed.

    This function must be idempotent, since it's called in a celery task. This function
    is responsible for updating all the state information in the database, such as
    tracking the appointment ID _if_ relevant. If no appointment should be registered
    because the submission form is not an appointment form, then this function just
    returns.

    :arg submission: :class:`Submission` instance containing all the relevant submission
      data.
    :raises AppointmentRegistrationFaild: if the submission form is an appointment form
      and registration was attempted. The state will already have been updated in the
      database with the relevant context/information - the exception just signals the
      failure to the caller so that it can retry if needed.
    """
    from .utils import book_appointment_for_submission

    book_appointment_for_submission(submission)
