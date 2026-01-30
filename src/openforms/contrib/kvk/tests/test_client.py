from django.test import SimpleTestCase, TestCase

import requests
import requests_mock
from privates.test import temp_private_root

from openforms.utils.tests.vcr import OFVCRMixin

from ..client import (
    NoServiceConfigured,
    get_kvk_branch_profile_client,
    get_kvk_profile_client,
    get_kvk_search_client,
)
from .base import KVKTestMixin


@temp_private_root()
class KVKSearchClientTests(OFVCRMixin, KVKTestMixin, SimpleTestCase):
    def test_client(self):
        with get_kvk_search_client() as client:
            # exists
            res = client.get_search_results({"kvkNummer": "69599084"})

        self.assertIsNotNone(res)
        self.assertIsNotNone(res["resultaten"])
        self.assertIsNotNone(res["resultaten"][0])
        self.assertEqual(res["resultaten"][0]["kvkNummer"], "69599084")

    def test_client_404(self):
        with get_kvk_search_client() as client:
            with self.assertRaises(requests.HTTPError):
                client.get_search_results({"kvkNummer": "12345678"})

    @requests_mock.Mocker()
    def test_client_500(self, m):
        m.get(requests_mock.ANY, status_code=500)

        with get_kvk_search_client() as client:
            with self.assertRaises(requests.RequestException):
                client.get_search_results({"kvkNummer": "69599084"})


@temp_private_root()
class KVKProfilesClientTests(OFVCRMixin, KVKTestMixin, SimpleTestCase):
    def test_client(self):
        with get_kvk_profile_client() as client:
            # exists
            res = client.get_profile("69599084")

        self.assertIsNotNone(res)
        self.assertEqual(res["kvkNummer"], "69599084")

    def test_client_vve(self):
        """
        Test response for a VVE-type company.

        Regression for #1299 where no "hoofdvestiging" data is present and address
        information must be sourced elsewhere.
        """

        with get_kvk_profile_client() as client:
            # exists
            res = client.get_profile("90000749")

        self.assertIsNotNone(res)
        self.assertEqual(res["kvkNummer"], "90000749")

    def test_client_404(self):
        with get_kvk_profile_client() as client:
            with self.assertRaises(requests.HTTPError):
                client.get_profile("12345678")

    @requests_mock.Mocker()
    def test_client_500(self, m):
        m.get(requests_mock.ANY, status_code=500)

        with get_kvk_profile_client() as client:
            with self.assertRaises(requests.RequestException):
                client.get_profile("69599084")


@temp_private_root()
class KVKBranchProfilesClientTests(OFVCRMixin, KVKTestMixin, TestCase):
    def test_client(self):
        with get_kvk_branch_profile_client() as client:
            res = client.get_profile("000038509504")

        self.assertIsNotNone(res)
        self.assertEqual(res["kvkNummer"], "69599084")
        self.assertEqual(res["vestigingsnummer"], "000038509504")

    def test_client_404(self):
        with get_kvk_branch_profile_client() as client:
            with self.assertRaises(requests.HTTPError):
                client.get_profile("12345678")

    def test_client_500(self):
        with self.vcr_raises(TimeoutError):
            with get_kvk_branch_profile_client() as client:
                with self.assertRaises(requests.RequestException):
                    client.get_profile("69599084")

    def test_client_without_service_configured(self):
        config = self.config_mock.return_value
        config.branch_profile_service = None

        with self.assertRaises(NoServiceConfigured):
            get_kvk_branch_profile_client()
