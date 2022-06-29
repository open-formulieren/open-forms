from unittest import skipIf
from unittest.mock import patch

from django.test import TestCase, tag

from openforms.registrations.exceptions import RegistrationFailed
from openforms.tests.utils import can_connect
from stuf.constants import EndpointType

from ...tests.factories import StufServiceFactory
from ..client import StufZDSClient


class StufZdsRegressionTests(TestCase):
    @tag("gh-1731")
    @skipIf(not can_connect("example.com:443"), "Need real socket/connection for test")
    def test_non_latin1_characters(self):
        """
        Regression test for non-latin1 characters in the XML body.

        We cannot mock the calls using requests_mock here as the crash happens inside
        http.client, used by requests.
        """
        stuf_service = StufServiceFactory.create()
        client = StufZDSClient(stuf_service, {})

        with patch.object(
            client.service, "get_endpoint", return_value="https://example.com"
        ):
            try:
                client._make_request(
                    template_name="stuf_zds/soap/creeerZaak.xml",
                    context={"referentienummer": "123", "extra": {"foo": "Ş"}},
                    endpoint_type=EndpointType.ontvang_asynchroon,
                )
            except UnicodeError:
                self.fail("Body encoding should succeed")
            except RegistrationFailed:
                pass
