from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase

import requests_mock
from glom import glom
from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.haal_centraal.constants import BRPVersions
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.contrib.haal_centraal.tests.utils import load_json_mock
from openforms.pre_requests.base import PreRequestHookBase
from openforms.pre_requests.registry import Registry
from openforms.submissions.tests.factories import SubmissionFactory

from ....constants import IdentifierRoles
from ..constants import AttributesV1 as DefaultAttributes
from ..plugin import (
    PLUGIN_IDENTIFIER,
    VERSION_TO_ATTRIBUTES_MAP,
    HaalCentraalPrefill,
    get_attributes_cls,
)


class AttributeResolutionTests(SimpleTestCase):
    def test_defined_attributes_paths_resolve(self):
        """
        Test that the attributes constant is compatible with the response data.
        """
        mock_files = {
            BRPVersions.v13: "ingeschrevenpersonen.v1-full.json",
            BRPVersions.v20: "ingeschrevenpersonen.v2-full-find-personen-response.json",
        }

        for version, attributes in VERSION_TO_ATTRIBUTES_MAP.items():
            with self.subTest(version=version):
                data = load_json_mock(mock_files[version])
                for key in sorted(attributes):
                    with self.subTest(key):
                        glom(data, key)

    def test_get_available_attributes(self):
        service = ServiceFactory.build()
        for version in BRPVersions:
            with self.subTest(version=version):
                config = HaalCentraalConfig(
                    brp_personen_service=service, brp_personen_version=version
                )

                with patch(
                    "openforms.contrib.haal_centraal.models.HaalCentraalConfig.get_solo",
                    return_value=config,
                ):
                    attrs = HaalCentraalPrefill.get_available_attributes()

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
    version: BRPVersions

    # set in setUp
    config: HaalCentraalConfig

    def setUp(self):
        super().setUp()  # type: ignore

        # set up patcher for the configuration
        config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="https://personen/api/",
            ),
            brp_personen_version=self.version,
        )
        config_patcher = patch(
            "openforms.contrib.haal_centraal.models.HaalCentraalConfig.get_solo",
            return_value=config,
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)  # type: ignore

        # prepare a requests mock instance to wire up the mocks
        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.addCleanup(self.requests_mock.stop)  # type: ignore

    def test_get_available_attributes(self):
        attributes = HaalCentraalPrefill.get_available_attributes()

        expected = VERSION_TO_ATTRIBUTES_MAP[self.version].choices
        self.assertEqual(attributes, expected)  # type: ignore

    def test_prefill_values(self):
        Attributes = get_attributes_cls()
        submission = SubmissionFactory.create(auth_info__value="999990676")
        assert submission.is_authenticated
        plugin = HaalCentraalPrefill(PLUGIN_IDENTIFIER)

        values = plugin.get_prefill_values(
            submission,
            attributes=[Attributes.naam_voornamen, Attributes.naam_geslachtsnaam],
        )

        expected = {
            "naam.voornamen": "Cornelia Francisca",
            "naam.geslachtsnaam": "Wiegman",
        }
        self.assertEqual(values, expected)  # type: ignore

    def test_prefill_values_not_authenticated(self):
        Attributes = get_attributes_cls()
        submission = SubmissionFactory.create()
        assert not submission.is_authenticated
        plugin = HaalCentraalPrefill(PLUGIN_IDENTIFIER)

        values = plugin.get_prefill_values(
            submission,
            attributes=[Attributes.naam_voornamen, Attributes.naam_geslachtsnaam],
        )

        self.assertEqual(values, {})  # type: ignore

    def test_prefill_values_for_gemachtigde_by_bsn(self):
        Attributes = get_attributes_cls()
        submission = SubmissionFactory.create(
            auth_info__value="111111111",
            auth_info__is_digid_machtigen=True,
            auth_info__legal_subject_identifier_value="999990676",
        )
        assert submission.is_authenticated
        plugin = HaalCentraalPrefill(PLUGIN_IDENTIFIER)

        values = plugin.get_prefill_values(
            submission,
            attributes=[Attributes.naam_voornamen, Attributes.naam_geslachtsnaam],
            identifier_role=IdentifierRoles.authorizee,
        )

        self.assertEqual(
            values,
            {
                "naam.voornamen": "Cornelia Francisca",
                "naam.geslachtsnaam": "Wiegman",
            },
        )  # type: ignore

    def test_person_not_found_returns_empty(self):
        Attributes = get_attributes_cls()
        submission = SubmissionFactory.create(auth_info__value="999990676")
        assert submission.is_authenticated

        plugin = HaalCentraalPrefill(PLUGIN_IDENTIFIER)

        values = plugin.get_prefill_values(
            submission,
            attributes=[Attributes.naam_voornamen, Attributes.naam_geslachtsnaam],
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
            Attributes = get_attributes_cls()
            submission = SubmissionFactory.create(auth_info__value="999990676")
            plugin = HaalCentraalPrefill(PLUGIN_IDENTIFIER)

            plugin.get_prefill_values(
                submission,
                attributes=[Attributes.naam_voornamen, Attributes.naam_geslachtsnaam],
            )

            mock.assert_called_once()
            context = mock.call_args.kwargs["context"]
            self.assertIsNotNone(context)  # type: ignore

    def test_extract_authorizee_identifier_value(self):
        cases = (
            # new auth context data approach
            (
                SubmissionFactory.create(
                    auth_info__is_digid_machtigen=True,
                    auth_info__legal_subject_identifier_value="999333666",
                ),
                "999333666",
            ),
            # new auth context data, but not a BSN
            (
                SubmissionFactory.create(
                    auth_info__is_eh_bewindvoering=True,
                    auth_info__legal_subject_identifier_value="12345678",
                ),
                None,
            ),
        )
        plugin = HaalCentraalPrefill(PLUGIN_IDENTIFIER)

        for submission, expected in cases:
            with self.subTest(auth_context=submission.auth_info.to_auth_context_data()):
                identifier_value = plugin.get_identifier_value(
                    submission, IdentifierRoles.authorizee
                )

                self.assertEqual(identifier_value, expected)


class HaalCentraalFindPersonV1Tests(HaalCentraalPluginTests, TestCase):
    version = BRPVersions.v13

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

    def test_prefill_values_for_gemachtigde_by_bsn(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v1-full.json"),
        )
        super().test_prefill_values_for_gemachtigde_by_bsn()

    def test_pre_request_hooks_called(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v1-full.json"),
        )
        super().test_pre_request_hooks_called()


class HaalCentraalFindPersonV2Tests(HaalCentraalPluginTests, TestCase):
    version = BRPVersions.v20

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

    def test_prefill_values_for_gemachtigde_by_bsn(self):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v2-full.json"),
        )
        super().test_prefill_values_for_gemachtigde_by_bsn()

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

        config = HaalCentraalConfig(brp_personen_version="", brp_personen_service=None)
        config_patcher = patch(
            "openforms.contrib.haal_centraal.models.HaalCentraalConfig.get_solo",
            return_value=config,
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)  # type: ignore

    def test_get_available_attributes(self):
        attributes = HaalCentraalPrefill.get_available_attributes()

        self.assertEqual(attributes, DefaultAttributes.choices)

    def test_get_prefill_values(self):
        Attributes = get_attributes_cls()

        plugin = HaalCentraalPrefill(PLUGIN_IDENTIFIER)

        with self.subTest("unauthenticated submission"):
            submission = SubmissionFactory.build()
            assert not submission.is_authenticated

            values = plugin.get_prefill_values(
                submission, attributes=(Attributes.naam_voornamen,)
            )

            self.assertEqual(values, {})

        with self.subTest("authenticated submission"):
            submission = SubmissionFactory.create(auth_info__value="999990676")
            assert submission.is_authenticated

            values = plugin.get_prefill_values(
                submission, attributes=(Attributes.naam_voornamen,)
            )

            self.assertEqual(values, {})
