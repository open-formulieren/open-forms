from django.test import TestCase

import requests_mock
from requests import RequestException
from zds_client import ClientError
from zgw_consumers.test import mock_service_oas_get

from openforms.contrib.kvk.client import KVKProfileClient, KVKSearchClient
from openforms.contrib.kvk.tests.base import KVKTestMixin


class KVKSearchClientTestCase(KVKTestMixin, TestCase):
    @requests_mock.Mocker()
    def test_client(self, m):
        mock_service_oas_get(m, "https://companies/api/", service="zoeken_openapi")
        m.get(
            "https://companies/v1/zoeken?kvkNummer=69599084",
            status_code=200,
            json=self.load_json_mock("zoeken_response.json"),
        )

        client = KVKSearchClient()
        # exists
        res = client.query(kvkNummer=69599084)
        self.assertIsNotNone(res)
        self.assertIsNotNone(res["resultaten"])
        self.assertIsNotNone(res["resultaten"][0])
        self.assertEqual(res["resultaten"][0]["kvkNummer"], "69599084")

    @requests_mock.Mocker()
    def test_client_404(self, m):
        mock_service_oas_get(m, "https://companies/api/", service="zoeken_openapi")
        m.get(
            "https://companies/v1/zoeken?kvkNummer=69599084",
            status_code=404,
        )
        client = KVKSearchClient()
        with self.assertRaises(ClientError):
            client.query(kvkNummer=69599084)

    @requests_mock.Mocker()
    def test_client_500(self, m):
        mock_service_oas_get(m, "https://companies/api/", service="zoeken_openapi")
        m.get(
            "https://companies/v1/zoeken?kvkNummer=69599084",
            status_code=500,
        )
        client = KVKSearchClient()
        with self.assertRaises(RequestException):
            client.query(kvkNummer=69599084)


class KVKProfilesClientTestCase(KVKTestMixin, TestCase):
    @requests_mock.Mocker()
    def test_client(self, m):
        mock_service_oas_get(m, "https://basisprofiel/", service="basisprofiel_openapi")
        m.get(
            "https://basisprofiel/v1/basisprofielen/69599084",
            status_code=200,
            json=self.load_json_mock("basisprofiel_response.json"),
        )

        client = KVKProfileClient()
        # exists
        res = client.query(69599084)
        self.assertIsNotNone(res)
        self.assertEqual(res["kvkNummer"], "69599084")

    @requests_mock.Mocker()
    def test_client_vve(self, m):
        """
        Test response for a VVE-type company.

        Regression for #1299 where no "hoofdvestiging" data is present and address
        information must be sourced elsewhere.
        """
        mock_service_oas_get(m, "https://basisprofiel/", service="basisprofiel_openapi")
        m.get(
            "https://basisprofiel/v1/basisprofielen/90000749",
            status_code=200,
            json=self.load_json_mock("basisprofiel_response_vve.json"),
        )

        client = KVKProfileClient()
        # exists
        res = client.query(90000749)
        self.assertIsNotNone(res)
        self.assertEqual(res["kvkNummer"], "90000749")

    @requests_mock.Mocker()
    def test_client_404(self, m):
        mock_service_oas_get(m, "https://basisprofiel/", service="basisprofiel_openapi")
        m.get(
            "https://basisprofiel/v1/basisprofielen/69599084",
            status_code=404,
        )
        client = KVKProfileClient()
        with self.assertRaises(ClientError):
            client.query(kvkNummer=69599084)

    @requests_mock.Mocker()
    def test_client_500(self, m):
        mock_service_oas_get(m, "https://basisprofiel/", service="basisprofiel_openapi")
        m.get(
            "https://basisprofiel/v1/basisprofielen/69599084",
            status_code=500,
        )
        client = KVKProfileClient()
        with self.assertRaises(RequestException):
            client.query(kvkNummer=69599084)
