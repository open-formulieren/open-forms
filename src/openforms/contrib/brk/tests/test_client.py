from django.test import SimpleTestCase

import requests
import requests_mock
from privates.test import temp_private_root

from openforms.utils.tests.vcr import OFVCRMixin

from ..client import get_client
from .base import TEST_FILES, BRKTestMixin


@temp_private_root()
class BRKCadastralClientTests(BRKTestMixin, OFVCRMixin, SimpleTestCase):
    VCR_TEST_FILES = TEST_FILES

    def test_client(self):
        with get_client() as client:
            res = client.get_real_estate_by_address(
                {"postcode": "7361EW", "huisnummer": "21"}
            )

        self.assertEqual(
            res["_embedded"]["kadastraalOnroerendeZaken"][0]["identificatie"],
            "76870482570000",
        )

    def test_client_404(self):
        with get_client() as client:
            res = client.get_real_estate_by_address(
                {"postcode": "1234AB", "huisnummer": "1"}  # Does not exist
            )
            self.assertEqual(res["_embedded"], {})

    @requests_mock.Mocker()
    def test_client_500(self, m):
        m.get(requests_mock.ANY, status_code=500)

        with get_client() as client:
            with self.assertRaises(requests.RequestException):
                client.get_real_estate_by_address(
                    {"postcode": "1234AA", "huisnummer": "123"}
                )


@temp_private_root()
class BRKTitleholdersClientTests(BRKTestMixin, OFVCRMixin, SimpleTestCase):
    VCR_TEST_FILES = TEST_FILES

    def test_client(self):
        with get_client() as client:
            res = client.get_cadastral_titleholders_by_cadastral_id("76870482570000")

        bsns = [
            a["persoon"]["identificatie"]
            for a in res["_embedded"]["zakelijkGerechtigden"]
        ]

        self.assertEqual(bsns, ["71291440", "71303564", "999991905"])

    def test_client_404(self):
        with get_client() as client:
            with self.assertRaises(requests.HTTPError):
                client.get_cadastral_titleholders_by_cadastral_id("dummy")

    @requests_mock.Mocker()
    def test_client_500(self, m):
        m.get(requests_mock.ANY, status_code=500)

        with get_client() as client:
            with self.assertRaises(requests.RequestException):
                client.get_real_estate_by_address("cadastral_id")
