"""
The authentication context describes details of an authentication.

A data model is proposed in github.com/maykinmedia/authentication-context-schemas (
private repository), with a JSON schema to specify and validate it. Vendors are free
to store and exchange this data, as long as it can be reconstructed into an object
that passes validation.

The schema used in these tests is taken from the proposal above. It will be made public
at some point.
"""

from unittest.mock import patch

from django.test.testcases import SimpleTestCase

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels

from openforms.submissions.tests.factories import SubmissionFactory

from ..base import BasePlugin
from ..constants import (
    ActingSubjectIdentifierType,
    AuthAttribute,
    LegalSubjectIdentifierType,
)
from ..models import AuthInfo
from ..registry import Registry
from .mocks import Plugin
from .utils import AuthContextAssertMixin

register = Registry()
register("dummy")(Plugin)


class AuthContextDataTests(AuthContextAssertMixin, SimpleTestCase):
    def test_plain_digid_auth(self):
        auth_info = AuthInfo(
            submission=SubmissionFactory.build(),
            plugin="dummy",
            attribute=AuthAttribute.bsn,
            value="999991607",
            attribute_hashed=False,
            loa=DigiDAssuranceLevels.middle,
            legal_subject_identifier_type="",
            legal_subject_identifier_value="",
        )

        with patch("openforms.authentication.models.auth_registry", new=register):
            auth_context = auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)

    def test_digid_machtigen_auth(self):
        auth_info = AuthInfo(
            submission=SubmissionFactory.build(),
            plugin="dummy",
            attribute=AuthAttribute.bsn,
            value="999991607",
            attribute_hashed=False,
            loa=DigiDAssuranceLevels.high,
            legal_subject_identifier_type=LegalSubjectIdentifierType.bsn,
            legal_subject_identifier_value="999995224",
            mandate_context={
                "services": [{"id": "cd9baded-ac37-4650-a607-c01b7ceabf20"}]
            },
        )

        with patch("openforms.authentication.models.auth_registry", new=register):
            auth_context = auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)

    def test_plain_eherkenning_auth(self):
        auth_info = AuthInfo(
            submission=SubmissionFactory.build(),
            plugin="dummy",
            attribute=AuthAttribute.kvk,
            value="90002768",
            attribute_hashed=False,
            loa=AssuranceLevels.substantial,
            legal_subject_identifier_type="",
            legal_subject_identifier_value="",
            acting_subject_identifier_type=ActingSubjectIdentifierType.opaque,
            acting_subject_identifier_value=(
                "4B75A0EA107B3D36C82FD675B5B78CC2F181B22E33D85F2D4A5DA63452EE3018"
                "@2D8FF1EF10279BC2643F376D89835151"
            ),
        )

        with patch("openforms.authentication.models.auth_registry", new=register):
            auth_context = auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertNotIn("branchNumber", auth_context["authorizee"]["legalSubject"])

    def test_plain_eherkenning_auth_with_service_restriction(self):
        auth_info = AuthInfo(
            submission=SubmissionFactory.build(),
            plugin="dummy",
            attribute=AuthAttribute.kvk,
            value="90002768",
            attribute_hashed=False,
            loa=AssuranceLevels.substantial,
            legal_subject_identifier_type="",
            legal_subject_identifier_value="",
            legal_subject_service_restriction="123123123123",
            acting_subject_identifier_type=ActingSubjectIdentifierType.opaque,
            acting_subject_identifier_value=(
                "4B75A0EA107B3D36C82FD675B5B78CC2F181B22E33D85F2D4A5DA63452EE3018"
                "@2D8FF1EF10279BC2643F376D89835151"
            ),
        )

        with patch("openforms.authentication.models.auth_registry", new=register):
            auth_context = auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertIn("branchNumber", auth_context["authorizee"]["legalSubject"])

    def test_eherkenning_machtigen_bewindvoering_auth(self):
        auth_info = AuthInfo(
            submission=SubmissionFactory.build(),
            plugin="dummy",
            attribute=AuthAttribute.bsn,
            value="999991607",
            attribute_hashed=False,
            loa=AssuranceLevels.substantial,
            legal_subject_identifier_type=LegalSubjectIdentifierType.kvk,
            legal_subject_identifier_value="90002768",
            acting_subject_identifier_type=ActingSubjectIdentifierType.opaque,
            acting_subject_identifier_value=(
                "4B75A0EA107B3D36C82FD675B5B78CC2F181B22E33D85F2D4A5DA63452EE3018"
                "@2D8FF1EF10279BC2643F376D89835151"
            ),
            mandate_context={
                "role": "bewindvoerder",
                "services": [
                    {
                        "id": "urn:etoegang:DV:00000001002308836000:services:9113",
                        "uuid": "34085d78-21aa-4481-a219-b28d7f3282fc",
                    }
                ],
            },
        )

        with patch("openforms.authentication.models.auth_registry", new=register):
            auth_context = auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertNotIn("branchNumber", auth_context["authorizee"]["legalSubject"])

    def test_eherkenning_machtigen_bewindvoering_auth_with_service_restriction(self):
        auth_info = AuthInfo(
            submission=SubmissionFactory.build(),
            plugin="dummy",
            attribute=AuthAttribute.bsn,
            value="999991607",
            attribute_hashed=False,
            loa=AssuranceLevels.substantial,
            legal_subject_identifier_type=LegalSubjectIdentifierType.kvk,
            legal_subject_identifier_value="90002768",
            legal_subject_service_restriction="123123123123",
            acting_subject_identifier_type=ActingSubjectIdentifierType.opaque,
            acting_subject_identifier_value=(
                "4B75A0EA107B3D36C82FD675B5B78CC2F181B22E33D85F2D4A5DA63452EE3018"
                "@2D8FF1EF10279BC2643F376D89835151"
            ),
            mandate_context={
                "role": "bewindvoerder",
                "services": [
                    {
                        "id": "urn:etoegang:DV:00000001002308836000:services:9113",
                        "uuid": "34085d78-21aa-4481-a219-b28d7f3282fc",
                    }
                ],
            },
        )

        with patch("openforms.authentication.models.auth_registry", new=register):
            auth_context = auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertIn("branchNumber", auth_context["authorizee"]["legalSubject"])

    def test_plugin_with_manage_auth_context_raises_error_if_auth_info_to_auth_context_method_isnt_implemented(
        self,
    ):
        class FailingAuthContextPlugin(BasePlugin):
            verbose_name = "some human readable label"
            provides_auth = (AuthAttribute.bsn,)
            manage_auth_context = True

        register("failing-auth-context")(FailingAuthContextPlugin)

        auth_info = AuthInfo(
            plugin="failing-auth-context",
            attribute=AuthAttribute.bsn,
            value="999991607",
        )

        with self.assertRaises(NotImplementedError) as exc:
            with patch("openforms.authentication.models.auth_registry", new=register):
                auth_info.to_auth_context_data()
                self.assertEqual(
                    exc.exception.args[0],
                    "Subclasses must implement 'auth_info_to_auth_context'",
                )

    def test_plugin_with_manage_auth_context_calls_auth_info_to_auth_context(self):
        class CorrectAuthContextPlugin(BasePlugin):
            verbose_name = "some human readable label"
            provides_auth = (AuthAttribute.bsn,)
            manage_auth_context = True

            def auth_info_to_auth_context(self, auth_info: AuthInfo):  # type: ignore
                return {
                    "result": "custom auth_info_to_auth_context handling",
                }

        register("correct-auth-context")(CorrectAuthContextPlugin)

        auth_info = AuthInfo(
            plugin="correct-auth-context",
            attribute=AuthAttribute.bsn,
            value="999991607",
        )

        with patch("openforms.authentication.models.auth_registry", new=register):
            auth_context = auth_info.to_auth_context_data()

        self.assertEqual(
            auth_context,
            {
                "result": "custom auth_info_to_auth_context handling",
            },
        )

    def test_auth_info_to_auth_context_is_only_called_when_with_manage_auth_context_is_true(
        self,
    ):
        class UnusedAuthContextPlugin(BasePlugin):
            verbose_name = "some human readable label"
            provides_auth = (AuthAttribute.bsn,)
            manage_auth_context = False

            def auth_info_to_auth_context(self, auth_info: AuthInfo):
                raise AssertionError("should not have been called!")

        register("unused-auth-context")(UnusedAuthContextPlugin)

        auth_info = AuthInfo(
            plugin="unused-auth-context",
            attribute=AuthAttribute.bsn,
            value="999991607",
            loa=DigiDAssuranceLevels.high,
        )

        with patch("openforms.authentication.models.auth_registry", new=register):
            auth_context = auth_info.to_auth_context_data()

        # Because the plugin `manage_auth_context` is set to False, the default logic is
        # used.
        self.assertEqual(
            auth_context,
            {
                "source": "digid",
                "levelOfAssurance": DigiDAssuranceLevels.high,
                "authorizee": {
                    "legalSubject": {
                        "identifierType": "bsn",
                        "identifier": "999991607",
                    }
                },
            },
        )
