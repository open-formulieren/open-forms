from typing import List

from django.conf import settings

from openforms.submissions.models import SubmissionReport
from openforms.tokens import BaseTokenGenerator


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


submission_report_token_generator = SubmissionReportTokenGenerator()
