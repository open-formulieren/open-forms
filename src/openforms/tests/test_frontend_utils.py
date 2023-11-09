from django.test import TestCase

from openforms.frontend import get_frontend_redirect_url
from openforms.submissions.tests.factories import SubmissionFactory


class FrontendRedirectTests(TestCase):
    def test_frontend_redirect_no_hash(self):
        submission = SubmissionFactory.create(
            form_url="https://example.com/basepath",
        )

        redirect_url = get_frontend_redirect_url(
            submission, "stap", ("action_1", "action_2"), {"q": "dummy"}
        )

        self.assertURLEqual(
            redirect_url,
            "https://example.com/basepath?_action=stap&_action_args=action_1,action_2&q=dummy",
        )

    def test_frontend_redirect_hash(self):
        submission = SubmissionFactory.create(
            form_url="https://example.com/basepath#after_hash",
        )

        redirect_url = get_frontend_redirect_url(
            submission, "stap", ("action_1", "action_2"), {"q": "dummy"}
        )

        self.assertURLEqual(
            redirect_url,
            "https://example.com/basepath?_action=stap&_action_args=action_1,action_2&q=dummy",
        )
