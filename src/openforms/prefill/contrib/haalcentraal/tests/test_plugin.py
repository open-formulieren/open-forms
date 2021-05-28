import json
import os

from django.test import TestCase

import requests_mock

from openforms.prefill.contrib.haalcentraal.constants import Attributes
from openforms.prefill.contrib.haalcentraal.models import HaalCentraalConfig
from openforms.prefill.contrib.haalcentraal.plugin import HaalCentraalPrefill
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.objectpath import resolve_object_path


def load_json_mock(name):
    path = os.path.join(os.path.dirname(__file__), "files", name)
    with open(path, "r") as f:
        return json.load(f)


def load_binary_mock(name):
    path = os.path.join(os.path.dirname(__file__), "files", name)
    with open(path, "rb") as f:
        return f.read()


class HaalCentraalPrefillTest(TestCase):
    def test_defined_attributes_paths_resolve(self):
        data = load_json_mock("ingeschrevenpersonen.999990676.json")

        for key, label in Attributes.choices:
            with self.subTest(f"{label}: {key}"):
                resolve_object_path(data, key)

    @requests_mock.Mocker()
    def test_get_prefill_values(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        m.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.999990676.json"),
        )

        config = HaalCentraalConfig.get_solo()
        service = ServiceFactory(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )
        config.service = service
        config.save()

        submission = SubmissionFactory(bsn="999990676")
        values = HaalCentraalPrefill.get_prefill_values(
            submission, [Attributes.voornamen, Attributes.geslachtsnaam]
        )
        expected = {
            "_embedded__naam__voornamen": "Cornelia Francisca",
            "_embedded__naam__geslachtsnaam": "Wiegman",
        }
        self.assertEqual(values, expected)

    def test_get_available_attributes(self):
        attrs = HaalCentraalPrefill.get_available_attributes()
        self.assertIsInstance(attrs, tuple)
        self.assertIsInstance(attrs[0], tuple)
        self.assertEqual(len(attrs[0]), 2)
