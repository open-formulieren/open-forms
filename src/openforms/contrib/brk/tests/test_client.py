from django.test import SimpleTestCase

import requests
import requests_mock
from privates.test import temp_private_root

from openforms.utils.tests.vcr import OFVCRMixin

from ..client import get_client
from .base import TEST_FILES, BRKTestMixin


@temp_private_root()
class BRKCadastralClientTests(OFVCRMixin, BRKTestMixin, SimpleTestCase):
    VCR_TEST_FILES = TEST_FILES

    def test_client(self):

        with get_client() as client:
            res = client.get_cadastrals_by_address(
                {"postcode": "1234AA", "huisnummer": "123"}
            )

        self.assertEqual(
            res["_embedded"]["kadastraalOnroerendeZaken"][0]["identificatie"],
            "cadastral_id",
        )

    def test_client_404(self):
        with get_client() as client:
            with self.assertRaises(requests.HTTPError):
                client.get_cadastrals_by_address(
                    {"postcode": "dummy", "huisnummer": "dummy"}
                )

    @requests_mock.Mocker()
    def test_client_500(self, m):
        m.get(requests_mock.ANY, status_code=500)

        with get_client() as client:
            with self.assertRaises(requests.RequestException):
                client.get_cadastrals_by_address(
                    {"postcode": "1234AA", "huisnummer": "123"}
                )


@temp_private_root()
class BRKTitleholdersClientTests(OFVCRMixin, BRKTestMixin, SimpleTestCase):
    VCR_TEST_FILES = TEST_FILES

    def test_client(self):

        with get_client() as client:
            res = client.get_cadastral_titleholders_by_cadastral_id("cadastral_id")

        bsns = [
            a["persoon"]["identificatie"]
            for a in res["_embedded"]["zakelijkGerechtigden"]
        ]

        self.assertEqual(bsns, ["123456789"])

    def test_client_404(self):
        with get_client() as client:
            with self.assertRaises(requests.HTTPError):
                client.get_cadastral_titleholders_by_cadastral_id("dummy")

    @requests_mock.Mocker()
    def test_client_500(self, m):
        m.get(requests_mock.ANY, status_code=500)

        with get_client() as client:
            with self.assertRaises(requests.RequestException):
                client.get_cadastrals_by_address("cadastral_id")
