from typing import Literal
from unittest.mock import patch

from django.test import TestCase

import requests_mock
from glom import glom
from zgw_consumers.models import Service
from zgw_consumers.test import mock_service_oas_get

from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory

from ..constants import HaalCentraalVersion
from ..models import HaalCentraalConfig
from .utils import load_json_mock


class HaalCentraalFindPersonTests:
    """
    Mixin defining the actual tests to run for a particular client version.

    All client versions must support this set of functionality.

    You must implement the classmethod ``setUpTestData`` to create the relevant service,
    for which you can then mock the API calls.
    """

    # specify in subclasses
    version: HaalCentraalVersion
    schema_yaml_name: Literal["personen", "personen-v2"]

    # set in setUP
    service: Service
    config: HaalCentraalConfig

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
        self.requests_mock = requests_mock.Mocker(real_http=True)
        self.requests_mock.start()
        mock_service_oas_get(
            self.requests_mock,
            url=self.service.api_root,
            service=self.schema_yaml_name,
            oas_url=self.service.oas,
        )
        self.addCleanup(self.requests_mock.stop)  # type: ignore

    def find_person_succesfully_test(self):
        attributes = self.config.get_attributes()
        client = self.config.build_client()
        assert client is not None

        attributes = [attributes.naam_voornamen, attributes.naam_geslachtsnaam]
        raw_data = client.find_person("999990676", attributes=attributes)

        values = {attr: glom(raw_data, attr) for attr in attributes}
        expected = {
            "naam.voornamen": "Cornelia Francisca",
            "naam.geslachtsnaam": "Wiegman",
        }
        self.assertEqual(values, expected)  # type: ignore

    def find_person_unsuccesfully_test(self):
        attributes = self.config.get_attributes()
        client = self.config.build_client()
        assert client is not None

        attributes = [attributes.naam_voornamen, attributes.naam_geslachtsnaam]
        raw_data = client.find_person(bsn="999990676", attributes=attributes)

        self.assertIsNone(raw_data)  # type: ignore


class HaalCentraalFindPersonV1Test(HaalCentraalFindPersonTests, TestCase):
    version = HaalCentraalVersion.haalcentraal13
    schema_yaml_name = "personen"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )

    def test_find_person_succesfully(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v1.json"),
        )
        super().find_person_unsuccesfully_test()

    def test_find_person_unsuccesfully_resulting_in_500(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=500,
        )
        super().find_person_unsuccesfully_test()

    def test_find_person_succesfully(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=404,
        )
        super().find_person_unsuccesfully_test()


class HaalCentraalFindPersonV2Test(HaalCentraalFindPersonTests, TestCase):
    version = HaalCentraalVersion.haalcentraal20
    schema_yaml_name = "personen-v2"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )

    def test_find_person_succesfully(self):
        self.requests_mock.post(
            "https://personen/api/",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v2-full.json"),
        )
        super().find_person_unsuccesfully_test()

    def test_find_person_without_personen_key(self):
        self.requests_mock.post(
            "https://personen/api/",
            status_code=200,
            json=load_json_mock(
                "ingeschrevenpersonen.v2-full-find-personen-response.json"
            ),
        )
        super().find_person_unsuccesfully_test()

    def test_find_person_unsuccesfully_resulting_in_500(self):
        self.requests_mock.post(
            "https://personen/",
            status_code=500,
        )
        super().find_person_unsuccesfully_test()

    def test_find_person_succesfully(self):
        self.requests_mock.post(
            "https://personen/",
            status_code=404,
        )
        super().find_person_unsuccesfully_test()
