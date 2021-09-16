from datetime import timedelta
from typing import List

from django.utils import timezone

from openforms.submissions.models import Submission
from openforms.tokens import BaseTokenGenerator

from .models import AppointmentInfo


class SubmissionAppointmentTokenGenerator(BaseTokenGenerator):
    """
    Strategy object used to generate and check tokens for submission appointments.
    """

    key_salt = "openforms.appointments.tokens.SubmissionAppointmentTokenGenerator"

    def check_token(self, submission: Submission, token: str) -> bool:
        """
        Tokens are always invalid if the appointment time is in the past.
        """
        try:
            info = submission.appointment_info
        except AppointmentInfo.DoesNotExist:
            return False

        # appointments in the past can never be valid
        if info.start_time and timezone.now() > info.start_time:
            return False

        # defer to the base implementation for actual token parsing
        return super().check_token(submission, token)

    def get_token_timeout_days(self, submission: Submission) -> int:
        """
        Determine how many days the token is valid for.

        The token is considered valid if the date is before or equal to the date of the
        appointment.
        """
        info = submission.appointment_info
        delta = info.start_time - info.created
        assert delta > timedelta(0, 0), "Expected a positive delta"
        return delta.days + 1

    def get_hash_value_parts(self, submission: Submission) -> List[str]:
        return [
            str(submission.id),
            str(submission.uuid),
            str(submission.appointment_info.status),
            str(submission.appointment_info.start_time),
        ]


submission_appointment_token_generator = SubmissionAppointmentTokenGenerator()
