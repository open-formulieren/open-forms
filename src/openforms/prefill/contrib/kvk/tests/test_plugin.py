import json
import os

from django.test import TestCase

import requests_mock
from glom import PathAccessError, glom

from openforms.prefill.contrib.kvk.constants import Attributes
from openforms.prefill.contrib.kvk.models import KVKConfig
from openforms.prefill.contrib.kvk.plugin import KVK_KVKNumberPrefill
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.submissions.tests.factories import SubmissionFactory


def load_json_mock(name):
    path = os.path.join(os.path.dirname(__file__), "files", name)
    with open(path, "r") as f:
        return json.load(f)


def load_binary_mock(name):
    path = os.path.join(os.path.dirname(__file__), "files", name)
    with open(path, "rb") as f:
        return f.read()


class KVKPrefillTest(TestCase):
    def setUp(self):
        config = KVKConfig.get_solo()
        service = ServiceFactory(
            api_root="https://companies/",
            oas="https://companies/api/schema/openapi.yaml",
        )
        config.service = service
        config.save()

    def test_defined_attributes_paths_resolve(self):
        data = load_json_mock("companies.json")
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
        m.get(
            "https://companies/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("kvkapiprofileoas3.yml"),
        )
        m.get(
            "https://companies/api/v2/profile/companies?kvkNumber=69599084",
            status_code=200,
            json=load_json_mock("companies.json"),
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
        m.get(
            "https://companies/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("kvkapiprofileoas3.yml"),
        )
        m.get(
            "https://companies/api/v2/profile/companies?kvkNumber=69599084",
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
        m.get(
            "https://companies/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("kvkapiprofileoas3.yml"),
        )
        m.get(
            "https://companies/api/v2/profile/companies?kvkNumber=69599084",
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
