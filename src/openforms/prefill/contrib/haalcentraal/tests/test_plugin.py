from unittest.mock import patch

from django.test import TestCase

import requests_mock
from glom import glom

from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import Attributes, AttributesV2, HaalCentraalVersion
from ..models import HaalCentraalConfig
from ..plugin import HaalCentraalPrefill, get_config, get_correct_attributes
from .utils import load_binary_mock, load_json_mock


class HaalCentraalPrefillV1Test(TestCase):
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

        submission = SubmissionFactory(auth_info__value="999990676")
        values = HaalCentraalPrefill.get_prefill_values(
            submission,
            [Attributes.naam_voornamen, Attributes.naam_geslachtsnaam],
        )
        expected = {
            "naam.voornamen": "Cornelia Francisca",
            "naam.geslachtsnaam": "Wiegman",
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

        submission = SubmissionFactory(auth_info__value="999990676")
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

        submission = SubmissionFactory(auth_info__value="999990676")
        values = HaalCentraalPrefill.get_prefill_values(
            submission,
            [Attributes.naam_voornamen, Attributes.naam_geslachtsnaam],
        )
        expected = {}
        self.assertEqual(values, expected)


class HaalCentraalPrefillApiV2Test(TestCase):
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

    def test_defined_attributes_paths_resolve(self):
        data = load_json_mock("personen-full-response.json")
        for key, label in sorted(AttributesV2.choices, key=lambda o: o[0]):
            with self.subTest(key):
                glom(data["personen"][0], key)

    @requests_mock.Mocker()
    def test_get_prefill_values(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml",
            status_code=200,
            content=load_binary_mock("personen-v2.yaml"),
        )
        m.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock("personen-full-response.json"),
        )

        submission = SubmissionFactory(auth_info__value="999993653")
        values = HaalCentraalPrefill.get_prefill_values(
            submission,
            [AttributesV2.naam_voornamen, AttributesV2.naam_geslachtsnaam],
        )
        expected = {
            "naam.voornamen": "Suzanne",
            "naam.geslachtsnaam": "Moulin",
        }
        self.assertEqual(values, expected)

    @requests_mock.Mocker()
    def test_get_prefill_values_http_500(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml",
            status_code=200,
            content=load_binary_mock("personen-v2.yaml"),
        )
        m.post(
            "https://personen/api/personen",
            status_code=500,
        )

        submission = SubmissionFactory(auth_info__value="999993653")
        values = HaalCentraalPrefill.get_prefill_values(
            submission,
            [AttributesV2.naam_voornamen, AttributesV2.naam_geslachtsnaam],
        )
        expected = {}
        self.assertEqual(values, expected)

    @requests_mock.Mocker()
    def test_get_prefill_values_http_404(self, m):
        m.get(
            "https://personen/api/schema/openapi.yaml",
            status_code=200,
            content=load_binary_mock("personen-v2.yaml"),
        )
        m.post(
            "https://personen/api/personen",
            status_code=404,
        )

        submission = SubmissionFactory(auth_info__value="999993653")
        values = HaalCentraalPrefill.get_prefill_values(
            submission,
            [AttributesV2.naam_voornamen, AttributesV2.naam_geslachtsnaam],
        )
        expected = {}
        self.assertEqual(values, expected)


class HaalCentraalPrefillNoConfigTest(TestCase):
    @patch(
        "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
        return_value=HaalCentraalConfig(),
    )
    def test_get_prefill_values_without_config(self, mock_solo):
        submission = SubmissionFactory(auth_info__value="999990676")
        values = HaalCentraalPrefill.get_prefill_values(
            submission,
            [Attributes.naam_voornamen, Attributes.naam_geslachtsnaam],
        )
        self.assertEqual(values, {})


class HaalCentraalPrefillGetAvailableAtributesTest(TestCase):
    @patch(
        "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
        return_value=HaalCentraalConfig(),
    )
    def test_get_available_attributes_no_configured_version(self, mock_solo):
        attrs = HaalCentraalPrefill.get_available_attributes()
        self.assertIsInstance(attrs, list)
        self.assertIsInstance(attrs[0], tuple)
        self.assertEqual(len(attrs[0]), 2)

    def test_get_available_attributes_v1(self):
        with patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(
                version=HaalCentraalVersion.haalcentraal13,
                service=ServiceFactory(
                    api_root="https://personen/api/",
                    oas="https://personen/api/schema/openapi.yaml",
                ),
            ),
        ):
            attrs = HaalCentraalPrefill.get_available_attributes()
            self.assertIsInstance(attrs, list)
            self.assertIsInstance(attrs[0], tuple)
            self.assertEqual(len(attrs[0]), 2)

    def test_get_available_attributes_v2(self):
        with patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(
                version=HaalCentraalVersion.haalcentraal20,
                service=ServiceFactory(
                    api_root="https://personen/api/",
                    oas="https://personen/api/schema/openapi.yaml",
                ),
            ),
        ):
            attrs = HaalCentraalPrefill.get_available_attributes()
            self.assertIsInstance(attrs, list)
            self.assertIsInstance(attrs[0], tuple)
            self.assertEqual(len(attrs[0]), 2)


class HaalCentraalPluginConfigTest(TestCase):
    @patch(
        "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
        return_value=HaalCentraalConfig(),
    )
    def test_no_config(self, mock_solo):
        config = get_config()
        self.assertIsNone(config)

    def test_config_is_v1(self):
        with patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(
                version=HaalCentraalVersion.haalcentraal13,
                service=ServiceFactory(
                    api_root="https://personen/api/",
                    oas="https://personen/api/schema/openapi.yaml",
                ),
            ),
        ):
            config = get_config()
            self.assertIsNotNone(config)

    def test_config_is_v2(self):
        with patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(
                version=HaalCentraalVersion.haalcentraal20,
                service=ServiceFactory(
                    api_root="https://personen/api/",
                    oas="https://personen/api/schema/openapi.yaml",
                ),
            ),
        ):
            config = get_config()
            self.assertIsNotNone(config)


class HaalCentraalPluginAttributesTest(TestCase):
    @patch(
        "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
        return_value=HaalCentraalConfig(),
    )
    def test_no_config(self, mock_solo):
        attributes = get_correct_attributes()
        self.assertEqual(attributes, Attributes)

    def test_config_is_v1(self):
        with patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(
                version=HaalCentraalVersion.haalcentraal13,
                service=ServiceFactory(
                    api_root="https://personen/api/",
                    oas="https://personen/api/schema/openapi.yaml",
                ),
            ),
        ):
            attributes = get_correct_attributes()
            self.assertEqual(attributes, Attributes)

    def test_config_is_v2(self):
        with patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=HaalCentraalConfig(
                version=HaalCentraalVersion.haalcentraal20,
                service=ServiceFactory(
                    api_root="https://personen/api/",
                    oas="https://personen/api/schema/openapi.yaml",
                ),
            ),
        ):
            attributes = get_correct_attributes()
            self.assertEqual(attributes, AttributesV2)
