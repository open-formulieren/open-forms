from ..constants import SUBMISSIONS_SESSION_KEY, UPLOADS_SESSION_KEY
from ..models import Submission, TemporaryFileUpload


class SubmissionsMixin:
    def _add_submission_to_session(self, submission: Submission):
        session = self.client.session
        ids = session.get(SUBMISSIONS_SESSION_KEY, [])
        ids += [str(submission.uuid)]
        session[SUBMISSIONS_SESSION_KEY] = ids
        session.save()

    def _add_upload_to_session(self, upload: TemporaryFileUpload):
        session = self.client.session
        ids = session.get(UPLOADS_SESSION_KEY, [])
        ids += [str(upload.uuid)]
        session[UPLOADS_SESSION_KEY] = ids
        session.save()

    def _clear_session(self):
        session = self.client.session
        session[SUBMISSIONS_SESSION_KEY] = []
        session[UPLOADS_SESSION_KEY] = []
        session.save()

    def _get_session_submission_uuids(self):
        session = self.client.session
        return session.get(SUBMISSIONS_SESSION_KEY, [])
