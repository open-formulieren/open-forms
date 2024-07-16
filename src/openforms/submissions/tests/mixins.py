from rest_framework.reverse import reverse

from openforms.middleware import CSRF_TOKEN_HEADER_NAME
from openforms.utils.tests.cache import clear_caches

from ..constants import SUBMISSIONS_SESSION_KEY
from ..models import Submission


class SubmissionsMixin:
    def setUp(self):
        self.addCleanup(clear_caches)
        super().setUp()

    def _add_submission_to_session(self, submission: Submission):
        session = self.client.session
        ids = session.get(SUBMISSIONS_SESSION_KEY, [])
        ids += [str(submission.uuid)]
        session[SUBMISSIONS_SESSION_KEY] = ids
        session.save()

    def _clear_session(self):
        session = self.client.session
        session[SUBMISSIONS_SESSION_KEY] = []
        session.save()

    def _get_session_submission_uuids(self):
        session = self.client.session
        return session.get(SUBMISSIONS_SESSION_KEY, [])

    def _get_csrf_token(self, submission):
        url = reverse("api:form-detail", kwargs={"uuid_or_slug": submission.form.uuid})
        response = self.client.get(url)

        return response.headers.get(CSRF_TOKEN_HEADER_NAME)
