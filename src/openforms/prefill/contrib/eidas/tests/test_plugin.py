from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels

from openforms.authentication.service import AuthAttribute
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import Attributes
from ..plugin import EIDASPrefill


class EIDASPrefillTests(TestCase):
    def test_get_prefill_values(self):
        plugin = EIDASPrefill(identifier="eidas")

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
                Attributes.legal_identifier,
                Attributes.legal_identifier_type,
                Attributes.legal_first_name,
                Attributes.legal_family_name,
                Attributes.legal_date_of_birth,
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
        plugin = EIDASPrefill(identifier="eidas")

        submission = SubmissionFactory.create()
        assert not submission.is_authenticated

        values = plugin.get_prefill_values(
            submission,
            [
                Attributes.legal_identifier,
                Attributes.legal_first_name,
            ],
        )
        expected = {}
        self.assertEqual(values, expected)

    def test_get_prefill_values_not_authenticated_with_eidas(self):
        plugin = EIDASPrefill(identifier="eidas")

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
                Attributes.legal_identifier,
            ],
        )

        expected = {}
        self.assertEqual(values, expected)

    def test_get_available_attributes(self):
        plugin = EIDASPrefill(identifier="eidas")

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
