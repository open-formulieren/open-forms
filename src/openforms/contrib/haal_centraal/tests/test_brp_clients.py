from unittest.mock import patch

from django.test import SimpleTestCase

import requests_mock
from glom import glom

from zgw_consumers_ext.tests.factories import ServiceFactory

from ..clients import get_brp_client
from ..constants import BRPVersions
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
    version: BRPVersions

    # possibly override for different versions, but at least v1 and v2 support both of these
    attributes_to_query = (
        "naam.voornamen",
        "naam.geslachtsnaam",
    )

    def setUp(self):
        super().setUp()  # type: ignore

        # set up patcher for the configuration
        config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="https://personen/api/",
                oas="https://this.is.ignored",
            ),
            brp_personen_version=self.version,
        )
        config_patcher = patch(
            "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
            return_value=config,
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)  # type: ignore

        # prepare a requests mock instance to wire up the mocks
        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.addCleanup(self.requests_mock.stop)  # type: ignore

    def test_find_person_succesfully(self):
        with get_brp_client() as client:
            raw_data = client.find_person(
                "999990676", attributes=self.attributes_to_query
            )

        values = {attr: glom(raw_data, attr) for attr in self.attributes_to_query}
        expected = {
            "naam.voornamen": "Cornelia Francisca",
            "naam.geslachtsnaam": "Wiegman",
        }
        self.assertEqual(values, expected)  # type: ignore

    def test_person_not_found(self):
        with get_brp_client() as client:
            raw_data = client.find_person(
                bsn="999990676", attributes=self.attributes_to_query
            )

        self.assertIsNone(raw_data)  # type: ignore

    def test_find_person_server_error(self):
        self.requests_mock.register_uri(
            requests_mock.ANY,
            requests_mock.ANY,
            status_code=500,
        )

        with get_brp_client() as client:
            raw_data = client.find_person(
                bsn="999990676", attributes=self.attributes_to_query
            )

        self.assertIsNone(raw_data)  # type: ignore

    def test_default_client_context(self):
        client = get_brp_client()

        self.assertIsNone(client.pre_request_context)  # type: ignore


class HaalCentraalFindPersonV1Test(HaalCentraalFindPersonTests, SimpleTestCase):
    version = BRPVersions.v13

    def test_find_person_succesfully(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v1.json"),
        )
        super().test_find_person_succesfully()

    def test_person_not_found(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676", status_code=404
        )
        super().test_person_not_found()


class HaalCentraalFindPersonV2Test(HaalCentraalFindPersonTests, SimpleTestCase):
    version = BRPVersions.v20

    def test_find_person_succesfully(self):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v2-full.json"),
        )
        super().test_find_person_succesfully()

    def test_person_not_found(self):
        self.requests_mock.post("https://personen/api/personen", status_code=404)
        super().test_person_not_found()

    def test_find_person_without_personen_key(self):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock(
                "ingeschrevenpersonen.v2-full-find-personen-response.json"
            ),
        )
        super().test_person_not_found()
