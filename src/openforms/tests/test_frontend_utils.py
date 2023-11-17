import json

from django.test import TestCase

from furl import furl

from openforms.frontend import get_frontend_redirect_url
from openforms.submissions.tests.factories import SubmissionFactory


class FrontendRedirectTests(TestCase):
    def test_frontend_redirect_no_hash(self):
        submission = SubmissionFactory.create(
            form_url="https://example.com/basepath",
        )

        action_params = {"action_1": "arg_1", "action_2": "arg_2"}

        redirect_url = get_frontend_redirect_url(
            submission,
            "resume",
            action_params,
        )

        excpected_redirect_url = furl("https://example.com/basepath")
        excpected_redirect_url.add(
            {
                "_of_action": "resume",
                "_of_action_params": json.dumps(action_params),
            }
        )

        self.assertURLEqual(
            redirect_url,
            excpected_redirect_url.url,
        )

    def test_frontend_redirect_hash(self):
        submission = SubmissionFactory.create(
            form_url="https://example.com/basepath#after_hash",
        )

        action_params = {"action_1": "arg_1", "action_2": "arg_2"}

        redirect_url = get_frontend_redirect_url(
            submission,
            "resume",
            action_params,
        )

        excpected_redirect_url = furl("https://example.com/basepath")
        excpected_redirect_url.add(
            {
                "_of_action": "resume",
                "_of_action_params": json.dumps(action_params),
            }
        )

        self.assertURLEqual(
            redirect_url,
            excpected_redirect_url.url,
        )

    def test_frontend_redirect_special_chars(self):
        submission = SubmissionFactory.create(
            form_url="https://example.com/basepath",
        )

        action_params = {"action&=": " arg_1 +"}

        redirect_url = get_frontend_redirect_url(
            submission,
            "resume",
            action_params,
        )

        excpected_redirect_url = furl("https://example.com/basepath")
        excpected_redirect_url.add(
            {
                "_of_action": "resume",
                "_of_action_params": json.dumps(action_params),
            }
        )

        self.assertURLEqual(
            redirect_url,
            excpected_redirect_url.url,
        )

    def test_frontend_redirect_query_param(self):
        submission = SubmissionFactory.create(
            form_url="https://example.com/basepath?unrelated_query=1&_of_action=unrelated",
        )

        action_params = {"action": "arg"}

        redirect_url = get_frontend_redirect_url(
            submission,
            "resume",
            action_params,
        )

        excpected_redirect_url = furl("https://example.com/basepath")
        excpected_redirect_url.add(
            {
                "_of_action": "resume",
                "_of_action_params": json.dumps(action_params),
                "unrelated_query": "1",
            }
        )

        self.assertURLEqual(
            redirect_url,
            excpected_redirect_url.url,
        )
