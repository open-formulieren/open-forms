from unittest.mock import MagicMock, patch

from django.test import TestCase

from glom import glom
from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.haal_centraal.clients import get_brp_client
from openforms.contrib.haal_centraal.constants import BRPVersions
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.pre_requests.base import PreRequestHookBase
from openforms.pre_requests.registry import Registry
from openforms.prefill.contrib.haalcentraal_brp.constants import AttributesV2
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ....constants import IdentifierRoles
from ....exceptions import PrefillSkipped
from ..plugin import (
    PLUGIN_IDENTIFIER,
    HaalCentraalPrefill,
    get_attributes_cls,
)


class HaalCentraalFindPersonV2Tests(OFVCRMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="http://localhost:5010/haalcentraal/api/brp/",
                auth_type=AuthTypes.no_auth,
            ),
            brp_personen_version=BRPVersions.v20,
        )
        self.config_patcher = patch(
            "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
            return_value=self.config,
        )
        self.config_patcher.start()
        self.addCleanup(self.config_patcher.stop)

    def test_defined_attributes_paths_resolve(self):
        """
        Test that the attributes constant is compatible with the response data.
        This is only for a sample since we do not know which fields are populated
        for each person (not all of them are required).
        """
        sample_of_attributes = [
            AttributesV2.naam_voornamen,
            AttributesV2.naam_geslachtsnaam,
        ]

        with get_brp_client() as client:
            data = client.find_persons(["999990676"], attributes=sample_of_attributes)
            assert data is not None

            for key in sample_of_attributes:
                with self.subTest(key):
                    glom(data["999990676"], key)

    def test_get_available_attributes(self):
        attrs = HaalCentraalPrefill.get_available_attributes()

        self.assertIsInstance(attrs, list)
        self.assertIsInstance(attrs[0], tuple)  # pyright: ignore[reportIndexIssue]
        self.assertEqual(len(attrs[0]), 2)  # pyright: ignore[reportIndexIssue]

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
        self.assertEqual(values, expected)

    def test_prefill_values_not_authenticated(self):
        Attributes = get_attributes_cls()
        submission = SubmissionFactory.create()
        assert not submission.is_authenticated
        plugin = HaalCentraalPrefill(PLUGIN_IDENTIFIER)

        with self.assertRaises(PrefillSkipped):
            plugin.get_prefill_values(
                submission,
                attributes=[Attributes.naam_voornamen, Attributes.naam_geslachtsnaam],
            )

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
        )

    def test_person_not_found_returns_empty(self):
        Attributes = get_attributes_cls()
        submission = SubmissionFactory.create(auth_info__value="000009923")
        assert submission.is_authenticated

        plugin = HaalCentraalPrefill(PLUGIN_IDENTIFIER)

        values = plugin.get_prefill_values(
            submission,
            attributes=[Attributes.naam_voornamen, Attributes.naam_geslachtsnaam],
        )
        self.assertEqual(values, {})

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
            self.assertIsNotNone(context)

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

    def test_get_prefill_values_with_empty_config(self):
        self.config.brp_personen_version = ""
        self.config.brp_personen_service = None
        self.config.save()

        self.config_patcher = patch(
            "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
            return_value=self.config,
        )

        Attributes = get_attributes_cls()

        plugin = HaalCentraalPrefill(PLUGIN_IDENTIFIER)

        with self.subTest("unauthenticated submission"):
            submission = SubmissionFactory.build()
            assert not submission.is_authenticated

            values = plugin.get_prefill_values(
                submission, attributes=[str(Attributes.naam_voornamen)]
            )

            self.assertEqual(values, {})

        with self.subTest("authenticated submission"):
            submission = SubmissionFactory.create(auth_info__value="999990676")
            assert submission.is_authenticated

            values = plugin.get_prefill_values(
                submission, attributes=[str(Attributes.naam_voornamen)]
            )

            self.assertEqual(values, {})
