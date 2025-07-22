from django.test import TestCase
from django.test.client import RequestFactory

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels

from openforms.authentication.constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.authentication.contrib.yivi_oidc.config import YiviOptions
from openforms.authentication.registry import register
from openforms.authentication.tests.factories import (
    AttributeGroupFactory,
)

plugin = register["yivi_oidc"]


class YiviPluginTransformClaimsTest(TestCase):
    """
    Testing the Yivi plugin ``transform_claims`` function.
    """

    def test_transform_claims_for_bsn_without_additional_attributes_claims(self):
        plugin_options: YiviOptions = {
            "authentication_options": AuthAttribute.values,
            "additional_attributes_groups": [],
            "bsn_loa": "",
            "kvk_loa": "",
        }
        form_auth = plugin.transform_claims(
            plugin_options,
            {
                "bsn_claim": "123456789",
                "loa_claim": "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard",
            },
        )

        self.assertEqual(
            form_auth,
            {
                "plugin": "yivi_oidc",
                "additional_claims": {},
                "attribute": "bsn",
                "value": "123456789",
                "loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard",
            },
        )

    def test_transform_claims_for_kvk_without_additional_attributes_claims(self):
        plugin_options: YiviOptions = {
            "authentication_options": AuthAttribute.values,
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
                "loa": "unknown",
                "value": "dummy-set-by@openforms",
            },
        )

    def test_transform_claims_with_additional_attributes_claims(self):
        AttributeGroupFactory(name="foo_attribute", attributes=["attribute_name"])
        plugin_options: YiviOptions = {
            "authentication_options": AuthAttribute.values,
            "additional_attributes_groups": ["foo_attribute"],
            "bsn_loa": "",
            "kvk_loa": "",
        }
        form_auth = plugin.transform_claims(
            plugin_options, {"additional_claims": {"attribute_name": "attribute_value"}}
        )

        # Assert that pseudo is used as fallback identifying value
        self.assertEqual(
            form_auth,
            {
                "plugin": "yivi_oidc",
                "additional_claims": {"attribute_name": "attribute_value"},
                "attribute": "pseudo",
                "loa": "unknown",
                "value": "dummy-set-by@openforms",
            },
        )


class YiviPluginCheckRequirementsTest(TestCase):
    """
    Testing the Yivi plugin ``check_requirements`` function.

    Until we have a proper setup for Yivi auth_flow_callback tests, we need to
    test/validate the ``check_requirements`` manually. Once Yivi auth_flow_callback is
    possible, these tests should be replaced with an actual Yivi authentication test
    implementation.
    """

    def test_valid_check_requirements_for_pseudo_auth(self):
        request = RequestFactory().get("/")
        request.session = {
            FORM_AUTH_SESSION_KEY: {
                "loa": "unknown",
                "attribute": AuthAttribute.pseudo,
            }
        }

        plugin_options: YiviOptions = {
            "authentication_options": [
                AuthAttribute.pseudo,
                AuthAttribute.kvk,
                AuthAttribute.bsn,
            ],
            "additional_attributes_groups": [],
            "bsn_loa": DigiDAssuranceLevels.high,
            "kvk_loa": AssuranceLevels.high,
        }

        self.assertTrue(plugin.check_requirements(request, plugin_options))

    def test_valid_check_requirements_for_bsn_auth(self):
        request = RequestFactory().get("/")
        request.session = {
            FORM_AUTH_SESSION_KEY: {
                "loa": "unknown",
                "attribute": AuthAttribute.pseudo,
            }
        }
        plugin_options: YiviOptions = {
            "authentication_options": [
                AuthAttribute.pseudo,
                AuthAttribute.kvk,
                AuthAttribute.bsn,
            ],
            "additional_attributes_groups": [],
            "bsn_loa": DigiDAssuranceLevels.high,
            "kvk_loa": AssuranceLevels.high,
        }

        self.assertTrue(plugin.check_requirements(request, plugin_options))

    def test_invalid_check_requirements_for_bsn_auth_with_loa_below_plugin_requirement(
        self,
    ):
        request = RequestFactory().get("/")
        request.session = {
            FORM_AUTH_SESSION_KEY: {
                "loa": DigiDAssuranceLevels.substantial,
                "attribute": AuthAttribute.bsn,
            }
        }
        plugin_options: YiviOptions = {
            "authentication_options": [
                AuthAttribute.pseudo,
                AuthAttribute.kvk,
                AuthAttribute.bsn,
            ],
            "additional_attributes_groups": [],
            "bsn_loa": DigiDAssuranceLevels.high,
            "kvk_loa": AssuranceLevels.high,
        }

        self.assertFalse(plugin.check_requirements(request, plugin_options))

    def test_valid_check_requirements_for_kvk_auth(self):
        request = RequestFactory().get("/")
        request.session = {
            FORM_AUTH_SESSION_KEY: {
                "loa": AssuranceLevels.high,
                "attribute": AuthAttribute.kvk,
            }
        }
        plugin_options: YiviOptions = {
            "authentication_options": [
                AuthAttribute.pseudo,
                AuthAttribute.kvk,
                AuthAttribute.bsn,
            ],
            "additional_attributes_groups": [],
            "bsn_loa": DigiDAssuranceLevels.high,
            "kvk_loa": AssuranceLevels.high,
        }

        self.assertTrue(plugin.check_requirements(request, plugin_options))

    def test_invalid_check_requirements_for_kvk_auth_with_loa_below_plugin_requirement(
        self,
    ):
        request = RequestFactory().get("/")
        request.session = {
            FORM_AUTH_SESSION_KEY: {
                "loa": AssuranceLevels.substantial,
                "attribute": AuthAttribute.kvk,
            }
        }
        plugin_options: YiviOptions = {
            "authentication_options": [
                AuthAttribute.pseudo,
                AuthAttribute.kvk,
                AuthAttribute.bsn,
            ],
            "additional_attributes_groups": [],
            "bsn_loa": DigiDAssuranceLevels.high,
            "kvk_loa": AssuranceLevels.high,
        }

        self.assertFalse(plugin.check_requirements(request, plugin_options))
