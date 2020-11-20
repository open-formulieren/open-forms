from ..constants import SUBMISSIONS_SESSION_KEY
from ..models import Submission


class SubmissionsMixin:
    def _add_submission_to_session(self, submission: Submission):
        session = self.client.session
        session[SUBMISSIONS_SESSION_KEY] = [str(submission.uuid)]
        session.save()
