from django.test import TestCase

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.tests.factories import AttributeGroupFactory

from ..config import YiviOptionsSerializer


class YiviOptionsSerializerTest(TestCase):
    """
    Test validation of the Yivi options serializer.
    """

    def test_valid_empty_options(self):
        serializer = YiviOptionsSerializer(data={})

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_options": [],
                "additional_attributes_groups": [],
                "bsn_loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
                "kvk_loa": "urn:etoegang:core:assurance-class:loa3",
            },
        )

    def test_valid_filled_in_options(self):
        AttributeGroupFactory.create(name="some_group")
        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": [
                    AuthAttribute.bsn,
                    AuthAttribute.kvk,
                ],
                "additional_attributes_groups": ["some_group"],
                "bsn_loa": DigiDAssuranceLevels.high,
                "kvk_loa": AssuranceLevels.low,
            },
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_options": [
                    "bsn",
                    "kvk",
                ],
                "additional_attributes_groups": ["some_group"],
                "bsn_loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI",
                "kvk_loa": "urn:etoegang:core:assurance-class:loa2",
            },
        )

    def test_invalid_options_with_unknown_authentication_options(self):
        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": ["foobar"],
            },
        )

        self.assertFalse(serializer.is_valid())

        self.assertTrue("authentication_options" in serializer.errors)
        self.assertEqual(
            serializer.errors["authentication_options"][0][0].code, "invalid_choice"
        )

    def test_invalid_options_with_unknown_additional_attributes_groups(self):
        serializer = YiviOptionsSerializer(
            data={
                "additional_attributes_groups": ["some_unknown_group"],
            },
        )

        self.assertFalse(serializer.is_valid())

        self.assertTrue("additional_attributes_groups" in serializer.errors)
        self.assertEqual(
            serializer.errors["additional_attributes_groups"][0][0].code,
            "invalid_choice",
        )
