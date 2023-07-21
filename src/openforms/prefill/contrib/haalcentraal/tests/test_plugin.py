from typing import Literal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase

import requests_mock
from glom import glom
from zds_client.oas import schema_fetcher
from zgw_consumers.models import Service
from zgw_consumers.test import mock_service_oas_get

from openforms.pre_requests.base import PreRequestHookBase
from openforms.pre_requests.registry import Registry
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import Attributes, HaalCentraalVersion
from ..models import VERSION_TO_ATTRIBUTES_MAP, HaalCentraalConfig
from ..plugin import HaalCentraalPrefill
from .utils import load_json_mock


class AttributeResolutionTests(SimpleTestCase):
    def test_defined_attributes_paths_resolve(self):
        """
        Test that the attributes constant is compatible with the response data.
        """
        mock_files = {
            HaalCentraalVersion.haalcentraal13: "ingeschrevenpersonen.v1-full.json",
            HaalCentraalVersion.haalcentraal20: "ingeschrevenpersonen.v2-full-find-personen-response.json",
        }

        for version, attributes in VERSION_TO_ATTRIBUTES_MAP.items():
            with self.subTest(version=version):
                data = load_json_mock(mock_files[version])
                for key in sorted(attributes):
                    with self.subTest(key):
                        glom(data, key)

    def test_get_available_attributes(self):
        service = ServiceFactory.build()
        for version in HaalCentraalVersion:
            with self.subTest(version=version):
                config = HaalCentraalConfig(version=version, service=service)

                attrs = config.get_attributes().choices

                self.assertIsInstance(attrs, list)  # type: ignore
                self.assertIsInstance(attrs[0], tuple)  # type: ignore
                self.assertEqual(len(attrs[0]), 2)  # type: ignore


class HaalCentraalPluginTests:
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

        # set up patcher for the configuration
        self.config = HaalCentraalConfig(version=self.version, service=self.service)
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

        # ensure the schema cache is cleared before and after each test
        schema_fetcher.cache.clear()
        self.addCleanup(schema_fetcher.cache.clear)  # type: ignore

    def test_get_available_attributes(self):
        attributes = HaalCentraalPrefill.get_available_attributes()

        expected = VERSION_TO_ATTRIBUTES_MAP[self.version].choices
        self.assertEqual(attributes, expected)  # type: ignore

    def test_prefill_values(self):
        attributes = self.config.get_attributes()

        submission = SubmissionFactory.create(auth_info__value="999990676")
        assert submission.is_authenticated
        values = HaalCentraalPrefill.get_prefill_values(
            submission,
            attributes=[attributes.naam_voornamen, attributes.naam_geslachtsnaam],
        )
        expected = {
            "naam.voornamen": "Cornelia Francisca",
            "naam.geslachtsnaam": "Wiegman",
        }
        self.assertEqual(values, expected)  # type: ignore

    def test_person_not_found_returns_empty(self):
        attributes = self.config.get_attributes()
        submission = SubmissionFactory.create(auth_info__value="999990676")
        assert submission.is_authenticated

        values = HaalCentraalPrefill.get_prefill_values(
            submission,
            attributes=[attributes.naam_voornamen, attributes.naam_geslachtsnaam],
        )

        self.assertEqual(values, {})  # type: ignore

    def test_pre_request_hooks_called(self):
        pre_req_register = Registry()
        mock = MagicMock()

        @pre_req_register("test")
        class PreRequestHook(PreRequestHookBase):
            def __call__(self, *args, **kwargs):
                mock(*args, **kwargs)

        with patch("openforms.pre_requests.clients.registry", new=pre_req_register):
            attributes = self.config.get_attributes()
            submission = SubmissionFactory.create(auth_info__value="999990676")
            haalcentraal_plugin = register["haalcentraal"]

            haalcentraal_plugin.get_prefill_values(
                submission,
                attributes=[attributes.naam_voornamen, attributes.naam_geslachtsnaam],
            )

            mock.assert_called_once()
            context = mock.call_args.kwargs["context"]
            self.assertIsNotNone(context)  # type: ignore


class HaalCentraalFindPersonV1Tests(HaalCentraalPluginTests, TestCase):
    version = HaalCentraalVersion.haalcentraal13
    schema_yaml_name = "personen"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )

    def test_prefill_values(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v1-full.json"),
        )
        super().test_prefill_values()

    def test_person_not_found_returns_empty(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=404,
        )
        super().test_person_not_found_returns_empty()

    def test_pre_request_hooks_called(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v1-full.json"),
        )
        super().test_pre_request_hooks_called()


class HaalCentraalFindPersonV2Tests(HaalCentraalPluginTests, TestCase):
    version = HaalCentraalVersion.haalcentraal20
    schema_yaml_name = "personen-v2"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )

    def test_prefill_values(self):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v2-full.json"),
        )
        super().test_prefill_values()

    def test_person_not_found_returns_empty(self):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json={"personen": []},
        )
        super().test_person_not_found_returns_empty()

    def test_pre_request_hooks_called(self):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v2-full.json"),
        )
        super().test_pre_request_hooks_called()


class HaalCentraalEmptyConfigTests(TestCase):
    def setUp(self):
        super().setUp()

        self.config = HaalCentraalConfig(version="", service=None)
        config_patcher = patch(
            "openforms.prefill.contrib.haalcentraal.plugin.HaalCentraalConfig.get_solo",
            return_value=self.config,
        )
        self.config_mock = config_patcher.start()
        self.addCleanup(config_patcher.stop)  # type: ignore

    def test_get_available_attributes(self):
        attributes = HaalCentraalPrefill.get_available_attributes()

        self.assertEqual(attributes, Attributes.choices)

    def test_get_prefill_values(self):
        attributes = self.config.get_attributes()

        with self.subTest("unauthenticated submission"):
            submission = SubmissionFactory.build()
            assert not submission.is_authenticated
            values = HaalCentraalPrefill.get_prefill_values(
                submission, attributes=(attributes.naam_voornamen,)
            )

            self.assertEqual(values, {})

        with self.subTest("authenticated submission"):
            submission = SubmissionFactory.create(auth_info__value="999990676")
            assert submission.is_authenticated

            values = HaalCentraalPrefill.get_prefill_values(
                submission, attributes=(attributes.naam_voornamen,)
            )

            self.assertEqual(values, {})
