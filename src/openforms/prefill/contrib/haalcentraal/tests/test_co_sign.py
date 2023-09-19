from typing import Literal
from unittest.mock import patch

from django.test import TestCase

import requests_mock
from zgw_consumers.models import Service
from zgw_consumers.test import mock_service_oas_get

from openforms.prefill.contrib.haalcentraal.constants import HaalCentraalVersion
from openforms.submissions.tests.factories import SubmissionFactory
from zgw_consumers_ext.tests.factories import ServiceFactory

from ....co_sign import add_co_sign_representation
from ....models import PrefillConfig
from ....registry import register
from ..models import HaalCentraalConfig
from .utils import load_json_mock

plugin = register["haalcentraal"]


class CoSignPrefillTests:
    """
    Mixin defining the actual tests to run for a particular client version.

    All client versions must support this set of functionality.

    You must implement the classmethod ``setUpTestData`` to create the relevant service,
    for which you can then mock the API calls.
    """

    # specify in subclasses
    version: HaalCentraalVersion
    schema_yaml_name: Literal["personen", "personen-v2"]

    # set in setUp
    service: Service
    config: HaalCentraalConfig

    def setUp(self):
        super().setUp()  # type: ignore

        # mock out django-solo interface (we don't have to deal with caches then)
        co_sign_config_patcher = patch(
            "openforms.prefill.co_sign.PrefillConfig.get_solo",
            return_value=PrefillConfig(default_person_plugin=plugin.identifier),
        )
        co_sign_config_patcher.start()
        self.addCleanup(co_sign_config_patcher.stop)  # type: ignore

        # set up patcher for the configuration
        self.config = HaalCentraalConfig(version=self.version, service=self.service)
        haalcentraal_config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=self.config,
        )
        self.config_mock = haalcentraal_config_patcher.start()
        self.addCleanup(haalcentraal_config_patcher.stop)  # type: ignore

        # prepare a requests mock instance to wire up the mocks
        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        mock_service_oas_get(
            self.requests_mock,
            url=self.service.api_root,
            service=self.schema_yaml_name,
            oas_url=self.service.oas,
        )
        self.addCleanup(self.requests_mock.stop)  # type: ignore

    def test_store_names_on_co_sign_auth(self):
        submission = SubmissionFactory.create(
            co_sign_data={
                "plugin": plugin.identifier,
                "identifier": "999990676",
                "fields": {},
            }
        )

        add_co_sign_representation(submission, plugin.requires_auth)

        submission.refresh_from_db()
        expected = {
            "plugin": plugin.identifier,
            "identifier": "999990676",
            "representation": "C. F. Wiegman",
            "fields": {
                "naam.voornamen": "Cornelia Francisca",
                "naam.voorvoegsel": "",
                "naam.voorletters": "C. F.",
                "naam.geslachtsnaam": "Wiegman",
            },
        }
        self.assertEqual(submission.co_sign_data, expected)  # type: ignore

    def test_incomplete_data_returned(self):
        submission = SubmissionFactory.create(
            co_sign_data={
                "plugin": plugin.identifier,
                "identifier": "999990676",
                "fields": {},
            }
        )

        add_co_sign_representation(submission, plugin.requires_auth)

        submission.refresh_from_db()
        expected = {
            "plugin": plugin.identifier,
            "identifier": "999990676",
            "representation": "",
            "fields": {},
        }
        self.assertEqual(submission.co_sign_data, expected)  # type: ignore


class CoSignPrefillV1Tests(CoSignPrefillTests, TestCase):
    version = HaalCentraalVersion.haalcentraal13
    schema_yaml_name = "personen"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )

    def test_store_names_on_co_sign_auth(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v1-full.json"),
        )
        super().test_store_names_on_co_sign_auth()

    def test_incomplete_data_returned(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v1-incomplete.json"),
        )
        super().test_incomplete_data_returned()


class CoSignPrefillV2Tests(CoSignPrefillTests, TestCase):
    version = HaalCentraalVersion.haalcentraal20
    schema_yaml_name = "personen-v2"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )

    def test_store_names_on_co_sign_auth(self):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v2-full.json"),
        )
        super().test_store_names_on_co_sign_auth()

    def test_incomplete_data_returned(self):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v2-incomplete.json"),
        )
        super().test_incomplete_data_returned()


class CoSignPrefillEmptyConfigTests(TestCase):
    def setUp(self):
        super().setUp()

        # mock out django-solo interface (we don't have to deal with caches then)
        self.config = HaalCentraalConfig(version="", service=None)
        config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=self.config,
        )
        self.config_mock = config_patcher.start()
        self.addCleanup(config_patcher.stop)  # type: ignore

        co_sign_config_patcher = patch(
            "openforms.prefill.co_sign.PrefillConfig.get_solo",
            return_value=PrefillConfig(default_person_plugin=plugin.identifier),
        )
        co_sign_config_patcher.start()
        self.addCleanup(co_sign_config_patcher.stop)  # type: ignore

    def test_store_names_on_co_sign_auth(self):
        submission = SubmissionFactory.create(
            co_sign_data={
                "plugin": plugin.identifier,
                "identifier": "999990676",
                "fields": {},
            }
        )

        add_co_sign_representation(submission, plugin.requires_auth)

        submission.refresh_from_db()
        expected = {
            "plugin": plugin.identifier,
            "identifier": "999990676",
            "representation": "",
            "fields": {},
        }
        self.assertEqual(submission.co_sign_data, expected)
