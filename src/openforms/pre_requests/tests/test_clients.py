from unittest.mock import patch

from django.test import SimpleTestCase

import requests_mock
from zgw_consumers.test import mock_service_oas_get

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.nlx import DisableNLXRewritingMixin
from zgw_consumers_ext.tests.factories import ServiceFactory

from ..base import PreRequestHookBase
from ..clients import PreRequestClientContext
from ..registry import Registry


class PreRequestHooksTest(DisableNLXRewritingMixin, SimpleTestCase):
    def test_pre_request_hook(self):
        register = Registry()

        @register("test-hook")
        class PreRequestHook(PreRequestHookBase):
            def __call__(self, url, method, kwargs, context):
                kwargs.setdefault("headers", {})
                kwargs["headers"].update({"test": "test"})

        submission = SubmissionFactory.build()
        service = ServiceFactory.build(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )
        client = service.build_client()
        client.context = PreRequestClientContext(submission=submission)

        with requests_mock.Mocker() as m:
            mock_service_oas_get(
                m, url=service.api_root, oas_url=service.oas, service="personen"
            )

            m.get("https://personen/api/test/path", status_code=200)

            with patch("openforms.pre_requests.clients.registry", new=register):
                client.request(path="/api/test/path", operation="test")

            last_request = m.request_history[-1]

            self.assertIn("test", last_request.headers)
            self.assertEqual("test", last_request.headers["test"])
