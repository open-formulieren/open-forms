from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels

from openforms.authentication.service import AuthAttribute
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import Attributes
from ..plugin import EIDASCompanyPrefill


class EIDASCompanyPrefillTests(TestCase):
    def test_get_prefill_values(self):
        plugin = EIDASCompanyPrefill(identifier="eidas-company")

        submission = SubmissionFactory.create(
            auth_info__value="1234ABC",
            auth_info__plugin="eidas_company_oidc",
            auth_info__loa=AssuranceLevels.substantial,
            auth_info__attribute=AuthAttribute.pseudo,
            auth_info__mandate_context={},
            auth_info__legal_subject_identifier_value="1234ABC",
            auth_info__legal_subject_identifier_type="opaque",
            auth_info__acting_subject_identifier_value="111222333",
            auth_info__acting_subject_identifier_type=AuthAttribute.bsn,
            auth_info__additional_claims={
                "first_name": "James",
                "family_name": "May",
                "date_of_birth": "1963-01-16",
                "company_name": "Top Gear",
            },
        )
        values = plugin.get_prefill_values(
            submission,
            [
                Attributes.legal_identifier,
                Attributes.legal_company_name,
                Attributes.acting_identifier,
                Attributes.acting_identifier_type,
                Attributes.acting_first_name,
                Attributes.acting_family_name,
                Attributes.acting_date_of_birth,
                "invalidAttribute",
            ],
        )
        expected = {
            "legalSubject.identifier": "1234ABC",
            "legalSubject.companyName": "Top Gear",
            "actingSubject.identifier": "111222333",
            "actingSubject.identifierType": AuthAttribute.bsn,
            "actingSubject.firstName": "James",
            "actingSubject.familyName": "May",
            "actingSubject.dateOfBirth": "1963-01-16",
        }
        self.assertEqual(values, expected)

    def test_get_prefill_values_not_authenticated(self):
        plugin = EIDASCompanyPrefill(identifier="eidas_company")

        submission = SubmissionFactory.create()
        assert not submission.is_authenticated

        values = plugin.get_prefill_values(
            submission,
            [
                Attributes.legal_identifier,
                Attributes.legal_company_name,
            ],
        )
        expected = {}
        self.assertEqual(values, expected)

    def test_get_prefill_values_not_authenticated_with_eidas(self):
        plugin = EIDASCompanyPrefill(identifier="eidas_company")

        # User was authenticated with digid_oidc, instead of with eidas_company_oidc.
        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__plugin="digid_oidc",
            auth_info__loa=DigiDAssuranceLevels.substantial,
            auth_info__attribute=AuthAttribute.pseudo,
        )
        assert submission.is_authenticated

        values = plugin.get_prefill_values(
            submission,
            [
                Attributes.legal_identifier,
            ],
        )

        expected = {}
        self.assertEqual(values, expected)

    def test_get_available_attributes(self):
        plugin = EIDASCompanyPrefill(identifier="eidas_company")

        attrs = plugin.get_available_attributes()

        self.assertEqual(
            attrs,
            [
                ("legalSubject.identifier", _("Legal subject > Identifier")),
                ("legalSubject.companyName", _("Legal subject > Company name")),
                ("actingSubject.identifier", _("Acting subject > Identifier")),
                ("actingSubject.identifierType", _("Acting subject > Identifier type")),
                ("actingSubject.firstName", _("Acting subject > First name")),
                ("actingSubject.familyName", _("Acting subject > Family name")),
                ("actingSubject.dateOfBirth", _("Acting subject > Date of birth")),
            ],
        )
