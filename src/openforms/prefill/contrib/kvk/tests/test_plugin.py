from django.test import TestCase

import requests_mock
from glom import PathAccessError, glom
from zgw_consumers.test import mock_service_oas_get

from openforms.contrib.kvk.tests.test_client import KVKTestMixin
from openforms.prefill.contrib.kvk.constants import Attributes
from openforms.prefill.contrib.kvk.plugin import KVK_KVKNumberPrefill
from openforms.submissions.tests.factories import SubmissionFactory


class KVKPrefillTest(KVKTestMixin, TestCase):
    def test_defined_attributes_paths_resolve(self):
        data = self.load_json_mock("companies.json")
        data = data["data"]["items"][0]
        for key, label in sorted(Attributes.choices, key=lambda o: o[0]):
            # TODO support array elements
            if "[]" in key:
                with self.subTest(key):
                    with self.assertRaises(PathAccessError):
                        glom(data, key)
            else:
                with self.subTest(key):
                    glom(data, key)

    @requests_mock.Mocker()
    def test_get_prefill_values(self, m):
        mock_service_oas_get(m, "https://companies/api/", service="kvkapiprofileoas3")
        m.get(
            "https://companies/api/v2/testprofile/companies?kvkNumber=69599084",
            status_code=200,
            json=self.load_json_mock("companies.json"),
        )

        plugin = KVK_KVKNumberPrefill(identifier="kvk")
        submission = SubmissionFactory(kvk="69599084")
        values = plugin.get_prefill_values(
            submission,
            [Attributes.legalForm, Attributes.tradeNames_businessName],
        )
        expected = {
            "tradeNames.businessName": "Test EMZ Dagobert",
            "legalForm": "Eenmanszaak",
        }
        self.assertEqual(values, expected)

    @requests_mock.Mocker()
    def test_get_prefill_values_404(self, m):
        mock_service_oas_get(m, "https://companies/api/", service="kvkapiprofileoas3")
        m.get(
            "https://companies/api/v2/testprofile/companies?kvkNumber=69599084",
            status_code=404,
        )

        plugin = KVK_KVKNumberPrefill(identifier="kvk")
        submission = SubmissionFactory(kvk="69599084")
        values = plugin.get_prefill_values(
            submission,
            [Attributes.legalForm, Attributes.tradeNames_businessName],
        )
        expected = {}
        self.assertEqual(values, expected)

    @requests_mock.Mocker()
    def test_get_prefill_values_500(self, m):
        mock_service_oas_get(m, "https://companies/api/", service="kvkapiprofileoas3")
        m.get(
            "https://companies/api/v2/testprofile/companies?kvkNumber=69599084",
            status_code=500,
        )

        plugin = KVK_KVKNumberPrefill(identifier="kvk")
        submission = SubmissionFactory(kvk="69599084")
        values = plugin.get_prefill_values(
            submission,
            [Attributes.legalForm, Attributes.tradeNames_businessName],
        )
        expected = {}
        self.assertEqual(values, expected)

    def test_get_available_attributes(self):
        plugin = KVK_KVKNumberPrefill(identifier="kvk")
        attrs = plugin.get_available_attributes()
        self.assertIsInstance(attrs, tuple)
        self.assertIsInstance(attrs[0], tuple)
        self.assertEqual(len(attrs[0]), 2)
