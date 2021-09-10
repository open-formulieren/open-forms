from datetime import date

from django.conf import settings
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36

from openforms.submissions.models import SubmissionReport


class SubmissionReportTokenGenerator:
    """
    Strategy object used to generate and check tokens for downloading submission reports.
    Implementation adapted from
    :class:`from django.contrib.auth.tokens.PasswordResetTokenGenerator`
    """

    key_salt = "openforms.submissions.tokens.SubmissionReportTokenGenerator"
    secret = settings.SECRET_KEY

    def make_token(self, submission_report: SubmissionReport) -> str:
        """
        Return a token that can be used once to download the submission report.
        """
        return self._make_token_with_timestamp(
            submission_report, self._num_days(date.today())
        )

    def check_token(self, submission_report: SubmissionReport, token: str) -> bool:
        """
        Check that the token is correct for a given submission report.
        """

        if not (submission_report and token):
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
        valid_token = self._make_token_with_timestamp(submission_report, ts)
        if not constant_time_compare(valid_token, token):
            return False

        # Check the timestamp is within limit. Timestamps are rounded to
        # midnight (server time) providing a resolution of only 1 day. If a
        # link is generated 5 minutes before midnight and used 6 minutes later,
        # that counts as 1 day. Therefore, SUBMISSION_REPORT_URL_TOKEN_TIMEOUT_DAYS = 1 means
        # "at least 1 day, could be up to 2."
        if (
            self._num_days(date.today()) - ts
        ) > settings.SUBMISSION_REPORT_URL_TOKEN_TIMEOUT_DAYS:
            return False

        return True

    def _make_token_with_timestamp(
        self, submission_report: SubmissionReport, timestamp: int
    ) -> str:
        # timestamp is number of days since 2001-1-1.  Converted to
        # base 36, this gives us a 3 digit string until about 2121
        ts_b36 = int_to_base36(timestamp)
        hash_string = salted_hmac(
            self.key_salt,
            self._make_hash_value(submission_report, timestamp),
            secret=self.secret,
        ).hexdigest()[
            ::2
        ]  # Limit to 20 characters to shorten the URL.
        return "%s-%s" % (ts_b36, hash_string)

    def _make_hash_value(
        self, submission_report: SubmissionReport, timestamp: int
    ) -> str:
        """
        Hash the submission report ID and some state properties.
        After a submission report has been downloaded, the state of the report is changed, so the token
        will no longer validate.
        Failing that, eventually settings.SUBMISSION_REPORT_URL_TOKEN_TIMEOUT_DAYS will
        invalidate the token.
        """
        submission_report_attributes = (
            "id",
            "last_accessed",
            "submission",
        )
        submission_report_bits = [
            str(getattr(submission_report, attribute) or "")
            for attribute in submission_report_attributes
        ]
        return "".join(submission_report_bits) + str(timestamp)

    def _num_days(self, dt) -> int:
        """
        Return the number of days between 01-01-2001 and today
        """
        return (dt - date(2001, 1, 1)).days


submission_report_token_generator = SubmissionReportTokenGenerator()

# deprecated - just keeping it around to not break imports
token_generator = submission_report_token_generator
