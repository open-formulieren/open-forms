from unittest.mock import patch

from django.test import SimpleTestCase

import requests_mock
from zgw_consumers.client import build_client
from zgw_consumers.nlx import NLXClient
from zgw_consumers.test.factories import ServiceFactory

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.nlx import DisableNLXRewritingMixin

from ..base import PreRequestHookBase
from ..clients import PreRequestClientContext, PreRequestMixin
from ..registry import Registry


class PreRequestsClient(PreRequestMixin, NLXClient):
    pass


class PreRequestHooksTest(DisableNLXRewritingMixin, SimpleTestCase):
    def test_pre_request_hook(self):
        register = Registry()

        @register("test-hook")
        class PreRequestHook(PreRequestHookBase):
            def __call__(self, url, method, kwargs, context=None):
                kwargs.setdefault("headers", {})
                kwargs["headers"].update({"test": "test"})

        submission = SubmissionFactory.build()
        service = ServiceFactory.build(api_root="https://personen/api/")
        client = build_client(
            service,
            client_factory=PreRequestsClient,
            context=PreRequestClientContext(submission=submission),
        )

        with (
            requests_mock.Mocker() as m,
            client,
        ):
            m.get("https://personen/api/test/path", status_code=200)

            with patch("openforms.pre_requests.clients.registry", new=register):
                client.get("test/path")

            last_request = m.request_history[-1]

            self.assertIn("test", last_request.headers)
            self.assertEqual("test", last_request.headers["test"])
