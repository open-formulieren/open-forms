from typing import Literal
from unittest.mock import patch

from django.test import TestCase

import requests_mock
from glom import glom
from zgw_consumers.models import Service
from zgw_consumers.test import mock_service_oas_get

from openforms.prefill.contrib.haalcentraal.plugin import HaalCentraalPrefill
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import HaalCentraalVersion
from ..models import HaalCentraalConfig
from .utils import load_json_mock


class HaalCentraalPluginTests:
    """
    Mixin defining the actual tests to run for a particular client version.

    All client versions must support this set of functionality.

    You must implement the classmethod ``setUpTestData`` to create the relevant service,
    for which you can then mock the API calls.
    """

    # specify in subclasses
    version: HaalCentraalVersion | None = None
    schema_yaml_name: Literal["personen", "personen-v2"] | None = None

    # set in setUP
    service: Service | None = None
    config: HaalCentraalConfig

    expected: any

    def setUp(self):
        super().setUp()  # type: ignore

        # set up patcher for the configuration
        self.config = HaalCentraalConfig(
            version=self.version,
            service=self.service,
        )
        config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=self.config,
        )
        self.config_mock = config_patcher.start()
        self.addCleanup(config_patcher.stop)  # type: ignore

        # prepare a requests mock instance to wire up the mocks
        if self.schema_yaml_name:
            self.requests_mock = requests_mock.Mocker(real_http=True)
            self.requests_mock.start()
            mock_service_oas_get(
                self.requests_mock,
                url=self.service.api_root,
                service=self.schema_yaml_name,
                oas_url=self.service.oas,
            )
            self.addCleanup(self.requests_mock.stop)  # type: ignore

    def defined_attributes_paths_resolve_test(self):
        attributes = self.config.get_attributes()

        data = load_json_mock(self.ingeschrevenpersonen)
        for key, label in sorted(attributes.choices, key=lambda o: o[0]):
            with self.subTest(key):
                glom(data, key)  # type: ignore

    def prefill_values_test(self):
        attributes = self.config.get_attributes()

        submission = SubmissionFactory(auth_info__value="999990676")
        values = HaalCentraalPrefill.get_prefill_values(
            submission,
            [attributes.naam_voornamen, attributes.naam_geslachtsnaam],
        )
        self.assertEqual(values, self.expected)  # type: ignore

    def attributes_values_test(self):
        attrs = HaalCentraalPrefill.get_available_attributes()
        self.assertIsInstance(attrs, list)  # type: ignore
        self.assertIsInstance(attrs[0], tuple)  # type: ignore
        self.assertEqual(len(attrs[0]), 2)  # type: ignore


class HaalCentraalFindPersonV1Test(HaalCentraalPluginTests, TestCase):
    version = HaalCentraalVersion.haalcentraal13
    schema_yaml_name = "personen"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )

    @patch(
        "openforms.prefill.contrib.haalcentraal.client.HaalCentraalV1Client.find_person",
        return_value=load_json_mock("ingeschrevenpersonen.v1-full.json"),
    )
    def test_prefill_returns_values(self, mock_find_person):
        self.expected = {
            "naam.voornamen": "Cornelia Francisca",
            "naam.geslachtsnaam": "Wiegman",
        }
        super().prefill_values_test()

    @patch(
        "openforms.prefill.contrib.haalcentraal.client.HaalCentraalV1Client.find_person",
        return_value={},
    )
    def test_prefill_find_person_returns_empty(self, mock_find_person):
        self.expected = {}
        super().prefill_values_test()

    def test_defined_attributes_paths_resolve(self):
        self.ingeschrevenpersonen = "ingeschrevenpersonen.v1-full.json"
        super().defined_attributes_paths_resolve_test()

    def test_attributes(self):
        super().attributes_values_test()


class HaalCentraalFindPersonV2Test(HaalCentraalPluginTests, TestCase):
    version = HaalCentraalVersion.haalcentraal20
    schema_yaml_name = "personen-v2"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )

    @patch(
        "openforms.prefill.contrib.haalcentraal.client.HaalCentraalV2Client.find_person",
        return_value=load_json_mock(
            "ingeschrevenpersonen.v2-full-find-personen-response.json"
        ),
    )
    def test_prefill_returns_values(self, mock_find_person):
        self.expected = {
            "naam.voornamen": "Cornelia Francisca",
            "naam.geslachtsnaam": "Wiegman",
        }
        super().prefill_values_test()

    @patch(
        "openforms.prefill.contrib.haalcentraal.client.HaalCentraalV2Client.find_person",
        return_value={},
    )
    def test_prefill_find_person_returns_empty(self, mock_find_person):
        self.expected = {}
        super().prefill_values_test()

    def test_defined_attributes_paths_resolve(self):
        self.ingeschrevenpersonen = (
            "ingeschrevenpersonen.v2-full-find-personen-response.json"
        )
        super().defined_attributes_paths_resolve_test()

    def test_attributes(self):
        super().attributes_values_test()


class HaalCentraalFindPersonNoConfigTest(HaalCentraalPluginTests, TestCase):
    def test_prefill_returns_values(self):
        self.expected = {}
        super().prefill_values_test()

    def test_attributes(self):
        super().attributes_values_test()
