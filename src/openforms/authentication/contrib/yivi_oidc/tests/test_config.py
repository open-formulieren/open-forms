from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.choices import DigiDAssuranceLevels

from ..config import YiviOptionsPolymorphicSerializer
from ..constants import YiviAuthenticationAttributes


class YiviOptionsPolymorphicSerializerTest(TestCase):
    """
    Test validation of the Yivi polymorphic options serializer.
    """

    def test_valid_options_for_bsn_without_loa(self):
        serializer = YiviOptionsPolymorphicSerializer(
            data={
                "authentication_attribute": YiviAuthenticationAttributes.bsn,
                "additional_scopes": [],
            },
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_attribute": YiviAuthenticationAttributes.bsn,
                "additional_scopes": [],
                "loa": DigiDAssuranceLevels.middle,
            },
        )

    def test_valid_options_for_bsn_with_loa(self):
        serializer = YiviOptionsPolymorphicSerializer(
            data={
                "authentication_attribute": YiviAuthenticationAttributes.bsn,
                "additional_scopes": [],
                "loa": DigiDAssuranceLevels.middle,
            },
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                "authentication_attribute": YiviAuthenticationAttributes.bsn,
                "additional_scopes": [],
                "loa": DigiDAssuranceLevels.middle,
            },
        )

    def test_invalid_options_without_authentication_attribute(self):
        serializer = YiviOptionsPolymorphicSerializer(
            data={
                "additional_scopes": [],
                "loa": DigiDAssuranceLevels.middle,
            },
        )

        with self.assertRaises(KeyError):
            self.assertFalse(serializer.is_valid())

        self.assertTrue("authentication_attribute" in serializer.errors)
        self.assertEqual(
            serializer.errors["authentication_attribute"][0].code, "required"
        )

    def test_invalid_options_with_unknown_authentication_attribute(self):
        serializer = YiviOptionsPolymorphicSerializer(
            data={
                "authentication_attribute": "foobar",
                "additional_scopes": [],
                "loa": DigiDAssuranceLevels.middle,
            },
        )

        with self.assertRaises(KeyError):
            self.assertFalse(serializer.is_valid())

        self.assertTrue("authentication_attribute" in serializer.errors)
        self.assertEqual(
            serializer.errors["authentication_attribute"][0].code, "invalid_choice"
        )

    def test_valid_options_with_additional_scopes(self):
        serializer = YiviOptionsPolymorphicSerializer(
            data={
                "authentication_attribute": YiviAuthenticationAttributes.bsn,
                "additional_scopes": ["some_scope", "foo", "bar:baz"],
            },
        )

        self.assertTrue(serializer.is_valid())

    def test_invalid_options_with_additional_scopes(self):
        serializer = YiviOptionsPolymorphicSerializer(
            data={
                "authentication_attribute": YiviAuthenticationAttributes.bsn,
                "additional_scopes": ["some invalid scope"],
                # A scope cannot contain spaces
            },
        )

        with self.assertRaises(KeyError):
            self.assertFalse(serializer.is_valid())

        self.assertTrue("additional_scopes" in serializer.errors)
        self.assertEqual(serializer.errors["additional_scopes"][0][0].code, "invalid")
        self.assertEqual(
            serializer.errors["additional_scopes"][0][0],
            _("The scope name cannot contain spaces."),
        )
