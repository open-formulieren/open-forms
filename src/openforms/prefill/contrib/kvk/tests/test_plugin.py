from django.test import TestCase

import requests_mock
from zgw_consumers.test import mock_service_oas_get

from openforms.contrib.kvk.tests.base import KVKTestMixin
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import Attributes
from ..plugin import KVK_KVKNumberPrefill


class KVKPrefillTest(KVKTestMixin, TestCase):
    @requests_mock.Mocker()
    def test_get_prefill_values(self, m):
        mock_service_oas_get(m, "https://basisprofiel/", service="basisprofiel_openapi")
        m.get(
            "https://basisprofiel/v1/basisprofielen/69599084",
            status_code=200,
            json=self.load_json_mock("basisprofiel_response.json"),
        )

        plugin = KVK_KVKNumberPrefill(identifier="kvk")
        submission = SubmissionFactory(kvk="69599084")
        values = plugin.get_prefill_values(
            submission,
            [Attributes.bezoekadres_straatnaam, Attributes.kvkNummer],
        )
        expected = {
            "bezoekadres.straatnaam": "Abebe Bikilalaan",
            "kvkNummer": "69599084",
        }
        self.assertEqual(values, expected)

    @requests_mock.Mocker()
    def test_get_prefill_values_vve(self, m):
        mock_service_oas_get(m, "https://basisprofiel/", service="basisprofiel_openapi")
        m.get(
            "https://basisprofiel/v1/basisprofielen/90000749",
            status_code=200,
            json=self.load_json_mock("basisprofiel_response_vve.json"),
        )

        plugin = KVK_KVKNumberPrefill(identifier="kvk")
        submission = SubmissionFactory(kvk="90000749")
        values = plugin.get_prefill_values(
            submission,
            [Attributes.bezoekadres_straatnaam, Attributes.kvkNummer],
        )
        expected = {
            "bezoekadres.straatnaam": "Blaauwweg",
            "kvkNummer": "90000749",
        }
        self.assertEqual(values, expected)

    @requests_mock.Mocker()
    def test_get_prefill_values_404(self, m):
        mock_service_oas_get(m, "https://basisprofiel/", service="basisprofiel_openapi")
        m.get(
            "https://basisprofiel/v1/basisprofielen/69599084",
            status_code=404,
        )

        plugin = KVK_KVKNumberPrefill(identifier="kvk")
        submission = SubmissionFactory(kvk="69599084")
        values = plugin.get_prefill_values(
            submission,
            [Attributes.bezoekadres_straatnaam, Attributes.kvkNummer],
        )
        expected = {}
        self.assertEqual(values, expected)

    @requests_mock.Mocker()
    def test_get_prefill_values_500(self, m):
        mock_service_oas_get(m, "https://basisprofiel/", service="basisprofiel_openapi")
        m.get(
            "https://basisprofiel/v1/basisprofielen/69599084",
            status_code=500,
        )

        plugin = KVK_KVKNumberPrefill(identifier="kvk")
        submission = SubmissionFactory(kvk="69599084")
        values = plugin.get_prefill_values(
            submission,
            [Attributes.bezoekadres_straatnaam, Attributes.kvkNummer],
        )
        expected = {}
        self.assertEqual(values, expected)

    def test_get_available_attributes(self):
        plugin = KVK_KVKNumberPrefill(identifier="kvk")
        attrs = plugin.get_available_attributes()
        self.assertIsInstance(attrs, tuple)
        self.assertIsInstance(attrs[0], tuple)
        self.assertEqual(len(attrs[0]), 2)
