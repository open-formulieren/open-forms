from unittest.mock import Mock, patch

from django.test import TestCase

import requests
from glom import glom

from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import HaalCentraalVersion
from ..models import HaalCentraalConfig
from .utils import load_json_mock


class BaseHaalCentraalTestFindPerson:
    class HaalCentraalFindPersonTest(TestCase):
        @patch(
            "zgw_consumers.client.ZGWClient.retrieve",
            return_value=load_json_mock("ingeschrevenpersonen.999990676.json"),
        )
        @patch(
            "zgw_consumers.client.ZGWClient.operation",
            return_value=load_json_mock("personen-full-api-response.json"),
        )
        def test_find_person_succesfully(self, mock_operation, mock_retrieve):
            with patch(
                "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
                return_value=HaalCentraalConfig(
                    version=self.version,
                    service=ServiceFactory(
                        api_root="https://personen/api/",
                        oas="https://personen/api/schema/openapi.yaml",
                    ),
                ),
            ):
                config = HaalCentraalConfig.get_solo()
                attributes = config.get_attributes()
                submission = SubmissionFactory(auth_info__value="999990676")
                attributes_list = [
                    attributes.naam_voornamen,
                    attributes.naam_geslachtsnaam,
                ]
                data = config.build_client().find_person(
                    submission,
                    (
                        attributes.naam_voornamen,
                        attributes.naam_geslachtsnaam,
                    ),
                )

                values = dict()

                if data:
                    for attr in attributes_list:
                        values[attr] = glom(data, attr)

                expected = {
                    "naam.voornamen": "Cornelia Francisca",
                    "naam.geslachtsnaam": "Wiegman",
                }
                self.assertEqual(values, expected)

        @patch(
            "zgw_consumers.client.ZGWClient.retrieve",
            side_effect=requests.HTTPError(Mock(status=500)),
        )
        @patch(
            "zgw_consumers.client.ZGWClient.operation",
            side_effect=requests.HTTPError(Mock(status=500)),
        )
        def test_find_person_500(self, mock_operation, mock_retrieve):
            with patch(
                "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
                return_value=HaalCentraalConfig(
                    version=self.version,
                    service=ServiceFactory(
                        api_root="https://personen/api/",
                        oas="https://personen/api/schema/openapi.yaml",
                    ),
                ),
            ):
                config = HaalCentraalConfig.get_solo()
                attributes = config.get_attributes()
                submission = SubmissionFactory(auth_info__value="999990676")
                data = config.build_client().find_person(
                    submission,
                    (
                        attributes.naam_voornamen,
                        attributes.naam_geslachtsnaam,
                    ),
                )

                self.assertIsNone(data)


class HaalCentraalFindPersonV1Test(
    BaseHaalCentraalTestFindPerson.HaalCentraalFindPersonTest
):
    def setUp(self):
        super().setUp()
        self.version = HaalCentraalVersion.haalcentraal13

    @patch(
        "zgw_consumers.client.ZGWClient.retrieve",
        side_effect=requests.HTTPError(Mock(status=404), "not found"),
    )
    def test_find_person_400(self, mock_retrieve):
        with patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(
                version=self.version,
                service=ServiceFactory(
                    api_root="https://personen/api/",
                    oas="https://personen/api/schema/openapi.yaml",
                ),
            ),
        ):
            config = HaalCentraalConfig.get_solo()
            submission = SubmissionFactory(auth_info__value="999990676")
            data = config.build_client().find_person(submission)

            self.assertIsNone(data)


class HaalCentraalFindPersonV2Test(
    BaseHaalCentraalTestFindPerson.HaalCentraalFindPersonTest
):
    def setUp(self):
        super().setUp()
        self.version = HaalCentraalVersion.haalcentraal20
