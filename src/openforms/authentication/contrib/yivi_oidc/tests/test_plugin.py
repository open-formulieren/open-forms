from django.test import TestCase

from openforms.authentication.contrib.yivi_oidc.config import YiviOptions
from openforms.authentication.contrib.yivi_oidc.constants import (
    YiviAuthenticationAttributes,
)
from openforms.authentication.registry import register
from openforms.authentication.tests.factories import AttributeGroupFactory

plugin = register["yivi_oidc"]


class YiviPluginTest(TestCase):
    """
    Test functionality of the Yivi plugin.
    """

    def test_get_user_chosen_authentication_attribute_when_all_authentication_options_are_allowed(
        self,
    ):
        claims_expected_result_map = (
            (
                {
                    "bsn_claim": "123456789",
                    "kvk_claim": "12345678",
                    "pseudo_claim": "hash",
                },
                YiviAuthenticationAttributes.bsn,
            ),
            (
                {"bsn_claim": "123456789", "kvk_claim": "12345678"},
                YiviAuthenticationAttributes.bsn,
            ),
            ({"bsn_claim": "123456789"}, YiviAuthenticationAttributes.bsn),
            (
                {"kvk_claim": "12345678", "pseudo_claim": "hash"},
                YiviAuthenticationAttributes.kvk,
            ),
            ({"kvk_claim": "12345678"}, YiviAuthenticationAttributes.kvk),
            ({"pseudo_claim": "hash"}, YiviAuthenticationAttributes.pseudo),
            ({}, YiviAuthenticationAttributes.pseudo),
        )
        for claims, expected_result in claims_expected_result_map:
            with self.subTest(data=claims, expected_result=expected_result):
                result = plugin._get_user_chosen_authentication_attribute(
                    YiviAuthenticationAttributes.values, claims
                )

                self.assertEqual(result, expected_result)

    def test_get_user_chosen_authentication_attribute_when_only_bsn_authentication_is_allowed(
        self,
    ):
        claims_expected_result_map = (
            ({"bsn_claim": "123456789"}, YiviAuthenticationAttributes.bsn),
            ({"kvk_claim": "12345678"}, YiviAuthenticationAttributes.pseudo),
            ({"pseudo_claim": "hash"}, YiviAuthenticationAttributes.pseudo),
            ({}, YiviAuthenticationAttributes.pseudo),
        )
        for claims, expected_result in claims_expected_result_map:
            with self.subTest(data=claims, expected_result=expected_result):
                result = plugin._get_user_chosen_authentication_attribute(
                    [YiviAuthenticationAttributes.bsn], claims
                )

                self.assertEqual(result, expected_result)

    def test_get_user_chosen_authentication_attribute_when_only_kvk_authentication_is_allowed(
        self,
    ):
        claims_expected_result_map = (
            ({"bsn_claim": "123456789"}, YiviAuthenticationAttributes.pseudo),
            ({"kvk_claim": "12345678"}, YiviAuthenticationAttributes.kvk),
            ({"pseudo_claim": "hash"}, YiviAuthenticationAttributes.pseudo),
            ({}, YiviAuthenticationAttributes.pseudo),
        )
        for claims, expected_result in claims_expected_result_map:
            with self.subTest(data=claims, expected_result=expected_result):
                result = plugin._get_user_chosen_authentication_attribute(
                    [YiviAuthenticationAttributes.kvk], claims
                )

                self.assertEqual(result, expected_result)

    def test_get_user_chosen_authentication_attribute_when_no_authentication_options_are_used(
        self,
    ):
        claims_expected_result_map = (
            ({"bsn_claim": "123456789"}, YiviAuthenticationAttributes.pseudo),
            ({"kvk_claim": "12345678"}, YiviAuthenticationAttributes.pseudo),
            ({"pseudo_claim": "hash"}, YiviAuthenticationAttributes.pseudo),
            ({}, YiviAuthenticationAttributes.pseudo),
        )
        for claims, expected_result in claims_expected_result_map:
            with self.subTest(data=claims, expected_result=expected_result):
                result = plugin._get_user_chosen_authentication_attribute([], claims)

                self.assertEqual(result, expected_result)

    def test_transform_claims_for_bsn_without_additional_attributes_claims(self):
        plugin_options: YiviOptions = {
            "authentication_options": YiviAuthenticationAttributes.values,
            "additional_attributes_groups": [],
            "bsn_loa": "",
            "kvk_loa": "",
        }
        form_auth = plugin.transform_claims(plugin_options, {"bsn_claim": "123456789"})

        self.assertEqual(
            form_auth,
            {
                "plugin": "yivi_oidc",
                "additional_claims": {},
                "attribute": "bsn",
                "value": "123456789",
                "loa": "",
            },
        )

    def test_transform_claims_for_kvk_without_additional_attributes_claims(self):
        plugin_options: YiviOptions = {
            "authentication_options": YiviAuthenticationAttributes.values,
            "additional_attributes_groups": [],
            "bsn_loa": "",
            "kvk_loa": "",
        }
        form_auth = plugin.transform_claims(plugin_options, {"kvk_claim": "12345678"})

        self.assertEqual(
            form_auth,
            {
                "plugin": "yivi_oidc",
                "additional_claims": {},
                "attribute": "kvk",
                "value": "12345678",
                "loa": "",
            },
        )

    def test_transform_claims_for_kvk_extended_without_additional_attributes_claims(
        self,
    ):
        plugin_options: YiviOptions = {
            "authentication_options": YiviAuthenticationAttributes.values,
            "additional_attributes_groups": [],
            "bsn_loa": "",
            "kvk_loa": "",
        }
        form_auth = plugin.transform_claims(
            plugin_options,
            {
                "kvk_claim": "12345678",
                "loa_claim": "urn:etoegang:core:assurance-class:loa2",
                "additional_claims": {},
            },
        )

        self.assertEqual(
            form_auth,
            {
                "plugin": "yivi_oidc",
                "additional_claims": {},
                "attribute": "kvk",
                "value": "12345678",
                "loa": "urn:etoegang:core:assurance-class:loa2",
            },
        )

    def test_transform_claims_for_pseudo_without_additional_attributes_claims(self):
        plugin_options: YiviOptions = {
            "authentication_options": YiviAuthenticationAttributes.values,
            "additional_attributes_groups": [],
            "bsn_loa": "",
            "kvk_loa": "",
        }
        form_auth = plugin.transform_claims(plugin_options, {})

        self.assertEqual(
            form_auth,
            {
                "plugin": "yivi_oidc",
                "additional_claims": {},
                "attribute": "pseudo",
                "value": "dummy-set-by@openforms",
            },
        )

    def test_transform_claims_without_authentication_or_additional_attributes(self):
        plugin_options: YiviOptions = {
            "authentication_options": [],
            "additional_attributes_groups": [],
            "bsn_loa": "",
            "kvk_loa": "",
        }
        form_auth = plugin.transform_claims(plugin_options, {})

        self.assertEqual(
            form_auth,
            {
                "plugin": "yivi_oidc",
                "additional_claims": {},
                "attribute": "pseudo",
                "value": "dummy-set-by@openforms",
            },
        )

    def test_transform_claims_with_additional_attributes_claims(self):
        AttributeGroupFactory(name="foo_attribute", attributes=["foo"])
        plugin_options: YiviOptions = {
            "authentication_options": YiviAuthenticationAttributes.values,
            "additional_attributes_groups": ["foo_attribute"],
            "bsn_loa": "",
            "kvk_loa": "",
        }
        form_auth = plugin.transform_claims(
            plugin_options, {"additional_claims": {"foo": "bar"}}
        )

        self.assertEqual(
            form_auth,
            {
                "plugin": "yivi_oidc",
                "additional_claims": {"foo": "bar"},
                "attribute": "pseudo",
                "value": "dummy-set-by@openforms",
            },
        )
