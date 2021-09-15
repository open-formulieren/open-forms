from typing import List

from django.conf import settings

from openforms.submissions.models import Submission, SubmissionReport
from openforms.tokens import BaseTokenGenerator

__all__ = ["submission_status_token_generator", "submission_report_token_generator"]


class SubmissionReportTokenGenerator(BaseTokenGenerator):
    """
    Strategy object used to generate and check tokens for downloading submission reports.
    """

    key_salt = "openforms.submissions.tokens.SubmissionReportTokenGenerator"
    token_timeout_days = settings.SUBMISSION_REPORT_URL_TOKEN_TIMEOUT_DAYS

    def get_hash_value_parts(self, submission_report: SubmissionReport) -> List[str]:
        submission_report_attributes = (
            "id",
            "last_accessed",
            "submission",
        )
        submission_report_bits = [
            str(getattr(submission_report, attribute) or "")
            for attribute in submission_report_attributes
        ]
        return submission_report_bits


class SubmissionStatusTokenGenerator(BaseTokenGenerator):
    key_salt = "openforms.submissions.tokens.SubmissionStatusTokenGenerator"
    # pin to the minimum of 1 day - the SDK should not be polling for longer than
    # about a minute anyway.
    token_timeout_days = 1

    def get_hash_value_parts(self, submission: Submission) -> List[str]:
        """
        Obtain the attribute values that mutate to invalidate the token.

        Technically this token is not single-use, as the status endpoint using this
        token is polled until processing has completed. However, if the on-completation
        chain was re-started (for example), the token is invalidated since it no longer
        represents the current state of execution.
        """
        attributes = [
            "completed_on",
            "suspended_on",
            "on_completion_task_id",
        ]
        return [str(getattr(submission, attr)) for attr in attributes]


submission_report_token_generator = SubmissionReportTokenGenerator()
submission_status_token_generator = SubmissionStatusTokenGenerator()
