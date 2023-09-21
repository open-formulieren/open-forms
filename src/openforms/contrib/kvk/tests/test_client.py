"""
TODO: replace with VCR tests against the public test environment.

Test env: https://developers.kvk.nl/documentation/testing
"""
from django.test import TestCase

import requests
import requests_mock

from ..client import get_client
from .base import KVKTestMixin, load_json_mock


class KVKSearchClientTestCase(KVKTestMixin, TestCase):
    @requests_mock.Mocker()
    def test_client(self, m):
        m.get(
            f"{self.api_root}v1/zoeken?kvkNummer=69599084",
            status_code=200,
            json=load_json_mock("zoeken_response.json"),
        )

        with get_client() as client:
            # exists
            res = client.get_search_results({"kvkNummer": "69599084"})

        self.assertIsNotNone(res)
        self.assertIsNotNone(res["resultaten"])
        self.assertIsNotNone(res["resultaten"][0])
        self.assertEqual(res["resultaten"][0]["kvkNummer"], "69599084")

    @requests_mock.Mocker()
    def test_client_404(self, m):
        m.get(
            f"{self.api_root}v1/zoeken?kvkNummer=69599084",
            status_code=404,
        )
        with get_client() as client:
            with self.assertRaises(requests.HTTPError):
                client.get_search_results({"kvkNummer": "69599084"})

    @requests_mock.Mocker()
    def test_client_500(self, m):
        m.get(
            f"{self.api_root}v1/zoeken?kvkNummer=69599084",
            status_code=500,
        )
        with get_client() as client:
            with self.assertRaises(requests.RequestException):
                client.get_search_results({"kvkNummer": "69599084"})


class KVKProfilesClientTestCase(KVKTestMixin, TestCase):
    @requests_mock.Mocker()
    def test_client(self, m):
        m.get(
            f"{self.api_root}v1/basisprofielen/69599084",
            json=load_json_mock("basisprofiel_response.json"),
        )

        with get_client() as client:
            # exists
            res = client.get_profile("69599084")

        self.assertIsNotNone(res)
        self.assertEqual(res["kvkNummer"], "69599084")

    @requests_mock.Mocker()
    def test_client_vve(self, m):
        """
        Test response for a VVE-type company.

        Regression for #1299 where no "hoofdvestiging" data is present and address
        information must be sourced elsewhere.
        """
        m.get(
            f"{self.api_root}v1/basisprofielen/90000749",
            json=load_json_mock("basisprofiel_response_vve.json"),
        )

        with get_client() as client:
            # exists
            res = client.get_profile("90000749")

        self.assertIsNotNone(res)
        self.assertEqual(res["kvkNummer"], "90000749")

    @requests_mock.Mocker()
    def test_client_404(self, m):
        m.get(
            f"{self.api_root}v1/basisprofielen/69599084",
            status_code=404,
        )
        with get_client() as client:
            with self.assertRaises(requests.HTTPError):
                client.get_profile("69599084")

    @requests_mock.Mocker()
    def test_client_500(self, m):
        m.get(
            f"{self.api_root}v1/basisprofielen/69599084",
            status_code=500,
        )
        with get_client() as client:
            with self.assertRaises(requests.RequestException):
                client.get_profile("69599084")
