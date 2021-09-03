from django.utils import timezone

from openforms.appointments.models import AppointmentInfo
from openforms.submissions.tokens import SubmissionTokenGenerator


class SubmissionAppointmentTokenGenerator(SubmissionTokenGenerator):
    """
    Used to generate and check tokens for submission appointments.
    """

    def get_expiry_days(self, submission):
        try:
            return (submission.appointment_info.start_time - timezone.now()).days
        except (AppointmentInfo.DoesNotExist, TypeError):
            return super().get_expiry_days(submission)


submission_appointment_token_generator = SubmissionAppointmentTokenGenerator()
