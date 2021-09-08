from datetime import date

from django.conf import settings
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36

from openforms.submissions.models import Submission


class SubmissionAppointmentTokenGenerator:
    """
    Strategy object used to generate and check tokens for submission appointments.
    Implementation adapted from
    :class:`from django.contrib.auth.tokens.PasswordResetTokenGenerator`
    """

    key_salt = "openforms.appointments.tokens.SubmissionAppointmentTokenGenerator"
    secret = settings.SECRET_KEY

    def make_token(self, submission: Submission) -> str:
        """
        Return a token that can be used to verify ownership of a submission.
        """
        return self._make_token_with_timestamp(submission, self._num_days(date.today()))

    def check_token(self, submission: Submission, token: str) -> bool:
        """
        Check that the token is correct for a given submission.
        """

        if not (submission and token):
            return False

        # parse the token
        try:
            ts_b36, _ = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        valid_token = self._make_token_with_timestamp(submission, ts)
        if not constant_time_compare(valid_token, token):
            return False

        expiry_days = (submission.appointment_info.start_time - timezone.now()).days

        # Check the timestamp is within limit. Timestamps are rounded to
        # midnight (server time) providing a resolution of only 1 day. If a
        # link is generated 5 minutes before midnight and used 6 minutes later,
        # that counts as 1 day. Therefore, SUBMISSION_TOKEN_TIMEOUT_DAYS = 1 means
        # "at least 1 day, could be up to 2."
        if (self._num_days(date.today()) - ts) > expiry_days:
            return False

        return True

    def _make_token_with_timestamp(self, submission: Submission, timestamp: int) -> str:
        # timestamp is number of days since 2001-1-1.  Converted to
        # base 36, this gives us a 3 digit string until about 2121
        ts_b36 = int_to_base36(timestamp)
        hash_string = salted_hmac(
            self.key_salt,
            self._make_hash_value(submission, timestamp),
            secret=self.secret,
        ).hexdigest()[
            ::2
        ]  # Limit to 20 characters to shorten the URL.
        return "%s-%s" % (ts_b36, hash_string)

    def _make_hash_value(self, submission: Submission, timestamp: int) -> str:
        submission_bits = [
            str(submission.id),
            str(submission.uuid),
            str(submission.appointment_info.status),
            str(submission.appointment_info.start_time),
        ]
        return "".join(submission_bits) + str(timestamp)

    def _num_days(self, dt) -> int:
        """
        Return the number of days between 01-01-2001 and today
        """
        return (dt - date(2001, 1, 1)).days


submission_appointment_token_generator = SubmissionAppointmentTokenGenerator()
