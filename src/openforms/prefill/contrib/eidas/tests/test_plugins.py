from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels

from openforms.authentication.service import AuthAttribute
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import CitizenAttributes, CompanyAttributes
from ..plugin import EIDASCitizenPrefill, EIDASCompanyPrefill


class EIDASCitizenTests(TestCase):
    def test_get_prefill_values(self):
        plugin = EIDASCitizenPrefill(identifier="eidas-citizen")

        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__plugin="eidas_oidc",
            auth_info__loa=AssuranceLevels.substantial,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__additional_claims={
                "first_name": "James",
                "family_name": "May",
                "date_of_birth": "1963-01-16",
            },
        )
        values = plugin.get_prefill_values(
            submission,
            [
                CitizenAttributes.legal_identifier,
                CitizenAttributes.legal_identifier_type,
                CitizenAttributes.legal_first_name,
                CitizenAttributes.legal_family_name,
                CitizenAttributes.legal_date_of_birth,
                "invalidAttribute",
            ],
        )
        expected = {
            "legalSubject.identifier": "111222333",
            "legalSubject.identifierType": AuthAttribute.bsn,
            "legalSubject.firstName": "James",
            "legalSubject.familyName": "May",
            "legalSubject.dateOfBirth": "1963-01-16",
        }
        self.assertEqual(values, expected)

    def test_get_prefill_values_not_authenticated(self):
        plugin = EIDASCitizenPrefill(identifier="eidas-citizen")

        submission = SubmissionFactory.create()
        assert not submission.is_authenticated

        values = plugin.get_prefill_values(
            submission,
            [
                CitizenAttributes.legal_identifier,
                CitizenAttributes.legal_first_name,
            ],
        )
        expected = {}
        self.assertEqual(values, expected)

    def test_get_prefill_values_not_authenticated_with_eidas(self):
        plugin = EIDASCitizenPrefill(identifier="eidas-citizen")

        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__plugin="digid_oidc",
            auth_info__loa=DigiDAssuranceLevels.substantial,
            auth_info__attribute=AuthAttribute.bsn,
        )
        assert submission.is_authenticated

        values = plugin.get_prefill_values(
            submission,
            [
                CitizenAttributes.legal_identifier,
            ],
        )

        expected = {}
        self.assertEqual(values, expected)

    def test_get_available_attributes(self):
        plugin = EIDASCitizenPrefill(identifier="eidas-citizen")

        attrs = plugin.get_available_attributes()

        self.assertEqual(
            attrs,
            [
                ("legalSubject.identifier", _("Legal subject > Identifier")),
                ("legalSubject.identifierType", _("Legal subject > Identifier type")),
                ("legalSubject.firstName", _("Legal subject > First name")),
                ("legalSubject.familyName", _("Legal subject > Family name")),
                ("legalSubject.dateOfBirth", _("Legal subject > Date of birth")),
            ],
        )


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
                CompanyAttributes.legal_identifier,
                CompanyAttributes.legal_company_name,
                CompanyAttributes.acting_identifier,
                CompanyAttributes.acting_identifier_type,
                CompanyAttributes.acting_first_name,
                CompanyAttributes.acting_family_name,
                CompanyAttributes.acting_date_of_birth,
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
        plugin = EIDASCompanyPrefill(identifier="eidas-company")

        submission = SubmissionFactory.create()
        assert not submission.is_authenticated

        values = plugin.get_prefill_values(
            submission,
            [
                CompanyAttributes.legal_identifier,
                CompanyAttributes.legal_company_name,
            ],
        )
        expected = {}
        self.assertEqual(values, expected)

    def test_get_prefill_values_not_authenticated_with_eidas(self):
        plugin = EIDASCompanyPrefill(identifier="eidas-company")

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
                CompanyAttributes.legal_identifier,
            ],
        )

        expected = {}
        self.assertEqual(values, expected)

    def test_get_available_attributes(self):
        plugin = EIDASCompanyPrefill(identifier="eidas-company")

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
