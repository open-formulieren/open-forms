from unittest.mock import patch

from django.test import TestCase

import requests_mock

from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ....co_sign import add_co_sign_representation
from ....models import PrefillConfig
from ....registry import register
from ..models import HaalCentraalConfig
from .utils import load_binary_mock, load_json_mock

plugin = register["haalcentraal"]


class CoSignPrefillTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )

    def setUp(self):
        super().setUp()

        # mock out django-solo interface (we don't have to deal with caches then)
        config_patcher = patch(
            "openforms.prefill.co_sign.PrefillConfig.get_solo",
            return_value=PrefillConfig(default_person_plugin=plugin.identifier),
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)

        hc_config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(service=self.service),
        )
        hc_config_patcher.start()
        self.addCleanup(hc_config_patcher.stop)

    @requests_mock.Mocker()
    def test_store_names_on_co_sign_auth(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            content=load_binary_mock("personen.yaml"),
        )
        m.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            json=load_json_mock("ingeschrevenpersonen.999990676.json"),
        )
        submission = SubmissionFactory.create(
            co_sign_data={
                "plugin": plugin.identifier,
                "identifier": "999990676",
                "fields": {},
            }
        )

        add_co_sign_representation(submission, plugin.requires_auth)

        submission.refresh_from_db()
        self.assertEqual(
            submission.co_sign_data,
            {
                "plugin": plugin.identifier,
                "identifier": "999990676",
                "representation": "C. F. Wiegman",
                "fields": {
                    "_embedded.naam.voornamen": "Cornelia Francisca",
                    "_embedded.naam.voorvoegsel": "",
                    "_embedded.naam.voorletters": "C. F.",
                    "_embedded.naam.geslachtsnaam": "Wiegman",
                },
            },
        )

    @requests_mock.Mocker()
    def test_incomplete_data_returned(self, m):
        # the API should not leave out those fields, but just to be on the safe side,
        # anticipate it
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            content=load_binary_mock("personen.yaml"),
        )
        m.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            json=load_json_mock("ingeschrevenpersonen.999990676-incomplete.json"),
        )
        submission = SubmissionFactory.create(
            co_sign_data={
                "plugin": plugin.identifier,
                "identifier": "999990676",
                "fields": {},
            }
        )

        add_co_sign_representation(submission, plugin.requires_auth)

        submission.refresh_from_db()
        self.assertEqual(
            submission.co_sign_data,
            {
                "plugin": plugin.identifier,
                "identifier": "999990676",
                "representation": "",
                "fields": {},
            },
        )
