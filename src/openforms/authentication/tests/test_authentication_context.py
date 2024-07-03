"""
The authentication context describes details of an authentication.

A data model is proposed in github.com/maykinmedia/authentication-context-schemas (
private repository), with a JSON schema to specify and validate it. Vendors are free
to store and exchange this data, as long as it can be reconstructed into an object
that passes validation.

The schema used in these tests is taken from the proposal above. It will be made public
at some point.
"""

from django.test import SimpleTestCase

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels

from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import (
    ActingSubjectIdentifierType,
    AuthAttribute,
    LegalSubjectIdentifierType,
)
from ..models import AuthInfo
from .utils import AuthContextAssertMixin


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

        auth_context = auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertIn("branchNumber", auth_context["authorizee"]["legalSubject"])
