from django.test import TestCase

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels

from openforms.authentication.tests.factories import AttributeGroupFactory

from ..config import YiviOptionsSerializer
from ..constants import YiviAuthenticationAttributes


class YiviOptionsSerializerTest(TestCase):
    """
    Test validation of the Yivi options serializer.
    """

    def test_valid_options_for_bsn_without_loa(self):
        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": [YiviAuthenticationAttributes.bsn],
                "additional_attributes_groups": [],
            },
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_options": [YiviAuthenticationAttributes.bsn],
                "additional_attributes_groups": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
                "kvk_loa": AssuranceLevels.substantial,
            },
        )

    def test_valid_options_for_bsn_with_loa(self):
        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": [YiviAuthenticationAttributes.bsn],
                "additional_attributes_groups": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
            },
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_options": [YiviAuthenticationAttributes.bsn],
                "additional_attributes_groups": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
                "kvk_loa": AssuranceLevels.substantial,
            },
        )

    def test_valid_options_for_kvk_without_loa(self):
        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": [YiviAuthenticationAttributes.kvk],
                "additional_attributes_groups": [],
            },
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_options": [YiviAuthenticationAttributes.kvk],
                "additional_attributes_groups": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
                "kvk_loa": AssuranceLevels.substantial,
            },
        )

    def test_valid_options_for_kvk_with_loa(self):
        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": [YiviAuthenticationAttributes.kvk],
                "additional_attributes_groups": [],
                "kvk_loa": AssuranceLevels.substantial,
            },
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_options": [YiviAuthenticationAttributes.kvk],
                "additional_attributes_groups": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
                "kvk_loa": AssuranceLevels.substantial,
            },
        )

    def test_invalid_options_with_unknown_authentication_options(self):
        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": ["foobar"],
                "additional_attributes_groups": [],
            },
        )

        self.assertFalse(serializer.is_valid())

        self.assertTrue("authentication_options" in serializer.errors)
        self.assertEqual(
            serializer.errors["authentication_options"][0][0].code, "invalid_choice"
        )

    def test_valid_options_for_bsn_with_additional_attributes_groups(self):
        AttributeGroupFactory(name="some_group")

        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": [YiviAuthenticationAttributes.bsn],
                "additional_attributes_groups": ["some_group"],
            },
        )

        self.assertTrue(serializer.is_valid())

    def test_valid_options_with_multiple_authentication_options(self):
        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": [
                    YiviAuthenticationAttributes.bsn,
                    YiviAuthenticationAttributes.kvk,
                ],
                "additional_attributes_groups": [],
            },
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_options": [
                    YiviAuthenticationAttributes.bsn,
                    YiviAuthenticationAttributes.kvk,
                ],
                "additional_attributes_groups": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
                "kvk_loa": AssuranceLevels.substantial,
            },
        )

    def test_valid_options_with_empty_authentication_options(self):
        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": [],
                "additional_attributes_groups": [],
            },
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_options": [],
                "additional_attributes_groups": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
                "kvk_loa": AssuranceLevels.substantial,
            },
        )

    def test_valid_options_with_no_authentication_options(self):
        serializer = YiviOptionsSerializer(
            data={
                "additional_attributes_groups": [],
            },
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_options": [],
                "additional_attributes_groups": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
                "kvk_loa": AssuranceLevels.substantial,
            },
        )
