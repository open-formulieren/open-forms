from typing import List

from django.utils import timezone

from openforms.submissions.models import Submission
from openforms.tokens import BaseTokenGenerator


class SubmissionAppointmentTokenGenerator(BaseTokenGenerator):
    """
    Strategy object used to generate and check tokens for submission appointments.
    """

    key_salt = "openforms.appointments.tokens.SubmissionAppointmentTokenGenerator"

    def get_token_timeout_days(self, submission: Submission) -> int:
        """
        Determine how many days the token is valid for.

        Defaults to :attr:`token_timeout_days`, optionally you can override this method and
        fetch information from the object being checked.
        """
        return (submission.appointment_info.start_time - timezone.now()).days

    def get_hash_value_parts(self, submission: Submission) -> List[str]:
        return [
            str(submission.id),
            str(submission.uuid),
            str(submission.appointment_info.status),
            str(submission.appointment_info.start_time),
        ]


submission_appointment_token_generator = SubmissionAppointmentTokenGenerator()
