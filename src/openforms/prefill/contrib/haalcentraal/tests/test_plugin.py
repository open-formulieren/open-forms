from django.test import TestCase

import requests_mock
from glom import glom

from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import Attributes
from ..models import HaalCentraalConfig
from ..plugin import HaalCentraalPrefill
from .utils import load_binary_mock, load_json_mock


class HaalCentraalPrefillTest(TestCase):
    def test_defined_attributes_paths_resolve(self):
        data = load_json_mock("ingeschrevenpersonen.999990676-full.json")
        for key, label in sorted(Attributes.choices, key=lambda o: o[0]):
            with self.subTest(key):
                glom(data, key)

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
            submission,
            [Attributes.naam_voornamen, Attributes.naam_geslachtsnaam],
        )
        expected = {
            "_embedded.naam.voornamen": "Cornelia Francisca",
            "_embedded.naam.geslachtsnaam": "Wiegman",
        }
        self.assertEqual(values, expected)

    @requests_mock.Mocker()
    def test_get_prefill_values_http_500(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        m.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=500,
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
            submission,
            [Attributes.naam_voornamen, Attributes.naam_geslachtsnaam],
        )
        expected = {}
        self.assertEqual(values, expected)

    @requests_mock.Mocker()
    def test_get_prefill_values_http_404(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        m.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=404,
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
            submission,
            [Attributes.naam_voornamen, Attributes.naam_geslachtsnaam],
        )
        expected = {}
        self.assertEqual(values, expected)

    def test_get_available_attributes(self):
        attrs = HaalCentraalPrefill.get_available_attributes()
        self.assertIsInstance(attrs, tuple)
        self.assertIsInstance(attrs[0], tuple)
        self.assertEqual(len(attrs[0]), 2)
