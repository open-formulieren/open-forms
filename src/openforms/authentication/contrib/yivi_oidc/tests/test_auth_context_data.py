from django.test import SimpleTestCase

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.models import AuthInfo
from openforms.authentication.tests.factories import AuthInfoFactory
from openforms.authentication.tests.utils import AuthContextAssertMixin

from ..constants import PLUGIN_ID


class YiviAuthContextUnitTests(AuthContextAssertMixin, SimpleTestCase):
    """
    Testing the AuthInfo ``to_auth_context_data`` functionality for Yivi.

    Due to e2e testing limitations, these tests only cover the ``to_auth_context_data``
    function.
    """

    def test_to_auth_context_data_for_bsn(self):
        auth_info: AuthInfo = AuthInfoFactory.build(
            plugin=PLUGIN_ID,
            attribute=AuthAttribute.bsn,
            value="111222333",
            loa=DigiDAssuranceLevels.middle,
            additional_claims={
                "firstName": "John",
                "familyName": "Doe",
            },
        )
        auth_context = auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(
            auth_context,
            {
                "source": "yivi",
                "authorizee": {
                    "legalSubject": {
                        "identifierType": "bsn",
                        "identifier": "111222333",
                        "additionalInformation": {
                            "firstName": "John",
                            "familyName": "Doe",
                        },
                    },
                },
                "levelOfAssurance": (
                    "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract"
                ),
            },
        )

    def test_to_auth_context_data_for_kvk(self):
        auth_info: AuthInfo = AuthInfoFactory.build(
            plugin=PLUGIN_ID,
            attribute=AuthAttribute.kvk,
            value="11122233",
            loa=AssuranceLevels.low,
            additional_claims={
                "firstName": "John",
                "familyName": "Doe",
            },
        )
        auth_context = auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(
            auth_context,
            {
                "source": "yivi",
                "authorizee": {
                    "legalSubject": {
                        "identifierType": "kvkNummer",
                        "identifier": "11122233",
                        "additionalInformation": {
                            "firstName": "John",
                            "familyName": "Doe",
                        },
                    },
                },
                "levelOfAssurance": "urn:etoegang:core:assurance-class:loa2",
            },
        )

    def test_to_auth_context_data_for_pseudo(self):
        auth_info: AuthInfo = AuthInfoFactory.build(
            plugin=PLUGIN_ID,
            attribute=AuthAttribute.pseudo,
            value="11122233",
            loa="unknown",
            additional_claims={
                "firstName": "John",
                "familyName": "Doe",
            },
        )
        auth_context = auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(
            auth_context,
            {
                "source": "yivi",
                "authorizee": {
                    "legalSubject": {
                        "identifierType": "opaque",
                        "identifier": "11122233",
                        "additionalInformation": {
                            "firstName": "John",
                            "familyName": "Doe",
                        },
                    }
                },
                "levelOfAssurance": "unknown",
            },
        )
