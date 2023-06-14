from unittest.mock import patch

from django.test import TestCase

import requests_mock
from glom import glom

from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import Attributes, AttributesV2, HaalCentraalVersion
from ..models import HaalCentraalConfig
from ..plugin import HaalCentraalPrefill, get_config
from .utils import load_binary_mock, load_json_mock


class BaseHaalCentraalTestCases:
    class BaseHaalCentraalTests(TestCase):
        def test_get_config(self):
            self.assertIsNotNone(get_config())

        def test_defined_attributes_paths_resolve(self):
            attributes = self.attributes
            data = load_json_mock(self.ingeschreven_personen_complete)
            for key, label in sorted(attributes.choices, key=lambda o: o[0]):
                with self.subTest(key):
                    glom(data, key)

        @requests_mock.Mocker()
        def test_get_prefill_values(self, m):
            attributes = self.attributes

            m.get(
                "https://personen/api/schema/openapi.yaml?v=3",
                status_code=200,
                content=load_binary_mock(self.personen),
            )
            with patch(
                f"openforms.prefill.contrib.haalcentraal.client.{self.client}.find_person",
                return_value=load_json_mock(self.ingeschreven_personen_complete),
            ):
                submission = SubmissionFactory(auth_info__value="999990676")
                values = HaalCentraalPrefill.get_prefill_values(
                    submission,
                    [attributes.naam_voornamen, attributes.naam_geslachtsnaam],
                )
                expected = {
                    "naam.voornamen": "Cornelia Francisca",
                    "naam.geslachtsnaam": "Wiegman",
                }
                self.assertEqual(values, expected)

        @requests_mock.Mocker()
        def test_get_prefill_values_http_500(self, m):
            attributes = self.attributes

            m.get(
                "https://personen/api/schema/openapi.yaml?v=3",
                status_code=200,
                content=load_binary_mock(self.personen),
            )
            with patch(
                f"openforms.prefill.contrib.haalcentraal.client.{self.client}.find_person",
                return_value=self.error_500,
            ):
                submission = SubmissionFactory(auth_info__value="999990676")
                values = HaalCentraalPrefill.get_prefill_values(
                    submission,
                    [attributes.naam_voornamen, attributes.naam_geslachtsnaam],
                )
                expected = {}
                self.assertEqual(values, expected)

        def test_get_attributes(self):
            attrs = HaalCentraalPrefill.get_available_attributes()
            self.assertIsInstance(attrs, list)
            self.assertIsInstance(attrs[0], tuple)
            self.assertEqual(len(attrs[0]), 2)


class HaalCentraalPrefilDefaultVersionTest(
    BaseHaalCentraalTestCases.BaseHaalCentraalTests
):
    def setUp(self):
        super().setUp()

        config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(
                service=ServiceFactory(
                    api_root="https://personen/api/",
                    oas="https://personen/api/schema/openapi.yaml",
                ),
            ),
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)

        self.attributes = Attributes

        self.personen = "personen.yaml"
        self.ingeschreven_personen_incomplete = "ingeschrevenpersonen.999990676.json"
        self.ingeschreven_personen_complete = "ingeschrevenpersonen.999990676-full.json"

        self.client = "HaalCentraalV1Client"
        self.error_404 = {
            "type": "https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.5",
            "title": "Opgevraagde resource bestaat niet.",
            "status": 404,
            "detail": "The server has not found anything matching the Request-URI.",
            "instance": "https://datapunt.voorbeeldgemeente.nl/api/v1/resourcenaam?parameter=waarde",
            "code": "notFound",
        }
        self.error_500 = {
            "type": "https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.5.1",
            "title": "Interne server fout.",
            "status": 500,
            "detail": "The server encountered an unexpected condition which prevented it from fulfilling the request.",
            "instance": "https://datapunt.voorbeeldgemeente.nl/api/v1/resourcenaam?parameter=waarde",
            "code": "serverError",
        }

    @requests_mock.Mocker()
    def test_get_prefill_values_http_404(self, m):
        attributes = self.attributes
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock(self.personen),
        )
        with patch(
            f"openforms.prefill.contrib.haalcentraal.client.{self.client}.find_person",
            return_value=self.error_404,
        ):
            submission = SubmissionFactory(auth_info__value="999990676")
            values = HaalCentraalPrefill.get_prefill_values(
                submission,
                [attributes.naam_voornamen, attributes.naam_geslachtsnaam],
            )
            expected = {}
            self.assertEqual(values, expected)


class HaalCentraalPrefillV1Test(BaseHaalCentraalTestCases.BaseHaalCentraalTests):
    def setUp(self):
        super().setUp()

        config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(
                version=HaalCentraalVersion.haalcentraal13,
                service=ServiceFactory(
                    api_root="https://personen/api/",
                    oas="https://personen/api/schema/openapi.yaml",
                ),
            ),
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)

        self.attributes = Attributes

        self.personen = "personen.yaml"
        self.ingeschreven_personen_incomplete = "ingeschrevenpersonen.999990676.json"
        self.ingeschreven_personen_complete = "ingeschrevenpersonen.999990676-full.json"

        self.client = "HaalCentraalV1Client"
        self.error_404 = {
            "type": "https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.5",
            "title": "Opgevraagde resource bestaat niet.",
            "status": 404,
            "detail": "The server has not found anything matching the Request-URI.",
            "instance": "https://datapunt.voorbeeldgemeente.nl/api/v1/resourcenaam?parameter=waarde",
            "code": "notFound",
        }
        self.error_500 = {
            "type": "https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.5.1",
            "title": "Interne server fout.",
            "status": 500,
            "detail": "The server encountered an unexpected condition which prevented it from fulfilling the request.",
            "instance": "https://datapunt.voorbeeldgemeente.nl/api/v1/resourcenaam?parameter=waarde",
            "code": "serverError",
        }

    @requests_mock.Mocker()
    def test_get_prefill_values_http_404(self, m):
        attributes = self.attributes
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock(self.personen),
        )
        with patch(
            f"openforms.prefill.contrib.haalcentraal.client.{self.client}.find_person",
            return_value=self.error_404,
        ):
            submission = SubmissionFactory(auth_info__value="999990676")
            values = HaalCentraalPrefill.get_prefill_values(
                submission,
                [attributes.naam_voornamen, attributes.naam_geslachtsnaam],
            )
            expected = {}
            self.assertEqual(values, expected)


class HaalCentraalPrefillV2Test(BaseHaalCentraalTestCases.BaseHaalCentraalTests):
    def setUp(self):
        super().setUp()

        config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(
                version=HaalCentraalVersion.haalcentraal20,
                service=ServiceFactory(
                    api_root="https://personen/api/",
                    oas="https://personen/api/schema/openapi.yaml",
                ),
            ),
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)

        self.attributes = AttributesV2

        self.personen = "personen-v2.yaml"
        self.ingeschreven_personen_incomplete = "personen-incomplete.json"
        self.ingeschreven_personen_complete = "personen-full-response.json"

        self.client = "HaalCentraalV2Client"
        self.error_500 = {
            "type": "https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.5.1",
            "title": "Interne server fout.",
            "status": 500,
            "detail": "The server encountered an unexpected condition which prevented it from fulfilling the request.",
            "instance": "https://datapunt.voorbeeldgemeente.nl/api/v1/resourcenaam?parameter=waarde",
            "code": "serverError",
        }


class HaalCentraalNoConfigTest(TestCase):
    def setUp(self):
        super().setUp()

        config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(),
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)

    def test_get_config(self):
        self.assertIsNone(get_config())

    def test_get_prefills(self):
        submission = SubmissionFactory(auth_info__value="999990676")
        values = HaalCentraalPrefill.get_prefill_values(
            submission,
            [Attributes.naam_voornamen, Attributes.naam_geslachtsnaam],
        )
        expected = {}
        self.assertEqual(values, expected)

    def test_get_attributes(self):
        attrs = HaalCentraalPrefill.get_available_attributes()
        self.assertIsInstance(attrs, list)
        self.assertIsInstance(attrs[0], tuple)
        self.assertEqual(len(attrs[0]), 2)
