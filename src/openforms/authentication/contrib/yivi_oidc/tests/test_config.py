from django.test import TestCase

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels

from openforms.authentication.tests.factories import AvailableScopeFactory

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
                "additional_scopes": [],
            },
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_options": [YiviAuthenticationAttributes.bsn],
                "additional_scopes": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
                "kvk_loa": AssuranceLevels.substantial,
            },
        )

    def test_valid_options_for_bsn_with_loa(self):
        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": [YiviAuthenticationAttributes.bsn],
                "additional_scopes": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
            },
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_options": [YiviAuthenticationAttributes.bsn],
                "additional_scopes": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
                "kvk_loa": AssuranceLevels.substantial,
            },
        )

    def test_valid_options_for_kvk_without_loa(self):
        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": [YiviAuthenticationAttributes.kvk],
                "additional_scopes": [],
            },
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_options": [YiviAuthenticationAttributes.kvk],
                "additional_scopes": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
                "kvk_loa": AssuranceLevels.substantial,
            },
        )

    def test_valid_options_for_kvk_with_loa(self):
        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": [YiviAuthenticationAttributes.kvk],
                "additional_scopes": [],
                "kvk_loa": AssuranceLevels.substantial,
            },
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_options": [YiviAuthenticationAttributes.kvk],
                "additional_scopes": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
                "kvk_loa": AssuranceLevels.substantial,
            },
        )

    def test_invalid_options_with_unknown_authentication_options(self):
        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": ["foobar"],
                "additional_scopes": [],
            },
        )

        self.assertFalse(serializer.is_valid())

        self.assertTrue("authentication_options" in serializer.errors)
        self.assertEqual(
            serializer.errors["authentication_options"][0][0].code, "invalid_choice"
        )

    def test_valid_options_for_bsn_with_additional_scopes(self):
        AvailableScopeFactory(scope="some_scope")
        AvailableScopeFactory(scope="foo")
        AvailableScopeFactory(scope="bar:baz")

        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": [YiviAuthenticationAttributes.bsn],
                "additional_scopes": ["some_scope", "foo", "bar:baz"],
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
                "additional_scopes": [],
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
                "additional_scopes": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
                "kvk_loa": AssuranceLevels.substantial,
            },
        )

    def test_valid_options_with_empty_authentication_options(self):
        serializer = YiviOptionsSerializer(
            data={
                "authentication_options": [],
                "additional_scopes": [],
            },
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_options": [],
                "additional_scopes": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
                "kvk_loa": AssuranceLevels.substantial,
            },
        )

    def test_valid_options_with_no_authentication_options(self):
        serializer = YiviOptionsSerializer(
            data={
                "additional_scopes": [],
            },
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_options": [],
                "additional_scopes": [],
                "bsn_loa": DigiDAssuranceLevels.middle,
                "kvk_loa": AssuranceLevels.substantial,
            },
        )
