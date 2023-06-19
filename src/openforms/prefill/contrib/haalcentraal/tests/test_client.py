from typing import Literal
from unittest.mock import patch

from django.test import SimpleTestCase

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

    You must implement the classmethod ``setUp`` to create the relevant service,
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
        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        mock_service_oas_get(
            self.requests_mock,
            url=self.service.api_root,
            service=self.schema_yaml_name,
            oas_url=self.service.oas,
        )
        self.addCleanup(self.requests_mock.stop)  # type: ignore

    def test_find_person_succesfully(self):
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

    def test_find_person_unsuccesfully(self):
        attributes = self.config.get_attributes()
        client = self.config.build_client()
        assert client is not None

        attributes = [attributes.naam_voornamen, attributes.naam_geslachtsnaam]
        raw_data = client.find_person(bsn="999990676", attributes=attributes)

        self.assertIsNone(raw_data)  # type: ignore

    def test_find_person_server_error(self):
        attributes = self.config.get_attributes()
        client = self.config.build_client()
        assert client is not None
        self.requests_mock.register_uri(
            requests_mock.ANY,
            requests_mock.ANY,
            additional_matcher=lambda request: "openapi.yaml" not in request.url,
            # additional_matcher=lambda request: "yaml" not in request.url,
            status_code=500,
        )

        attributes = [attributes.naam_voornamen, attributes.naam_geslachtsnaam]
        raw_data = client.find_person(bsn="999990676", attributes=attributes)

        self.assertIsNone(raw_data)  # type: ignore


class HaalCentraalFindPersonV1Test(HaalCentraalFindPersonTests, SimpleTestCase):
    version = HaalCentraalVersion.haalcentraal13
    schema_yaml_name = "personen"

    def setUp(self):
        self.service = ServiceFactory.build(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )
        super().setUp()

    def test_find_person_succesfully(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v1.json"),
        )
        super().test_find_person_succesfully()

    def test_find_person_unsuccesfully(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676", status_code=404
        )
        super().test_find_person_unsuccesfully()


class HaalCentraalFindPersonV2Test(HaalCentraalFindPersonTests, SimpleTestCase):
    version = HaalCentraalVersion.haalcentraal20
    schema_yaml_name = "personen-v2"

    def setUp(self):
        self.service = ServiceFactory.build(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )
        super().setUp()

    def test_find_person_succesfully(self):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v2-full.json"),
        )
        super().test_find_person_succesfully()

    def test_find_person_unsuccesfully(self):
        self.requests_mock.post("https://personen/api/personen", status_code=404)
        super().test_find_person_unsuccesfully()

    def test_find_person_without_personen_key(self):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock(
                "ingeschrevenpersonen.v2-full-find-personen-response.json"
            ),
        )
        super().test_find_person_unsuccesfully()
