from ..constants import SUBMISSIONS_SESSION_KEY
from ..models import Submission


class SubmissionsMixin:
    def _add_submission_to_session(self, submission: Submission):
        session = self.client.session
        ids = session.get(SUBMISSIONS_SESSION_KEY, [])
        ids += [str(submission.uuid)]
        session[SUBMISSIONS_SESSION_KEY] = ids
        session.save()
