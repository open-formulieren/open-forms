from django.test import TestCase
from django.test.client import RequestFactory

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels

from openforms.authentication.constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.authentication.contrib.yivi_oidc.config import YiviOptions
from openforms.authentication.contrib.yivi_oidc.models import (
    YiviOpenIDConnectConfig,
)
from openforms.authentication.contrib.yivi_oidc.tests.base import mock_yivi_config
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


class YiviPluginBeforeProcessClaimsTest(TestCase):
    """
    Testing the Yivi plugin ``before_process_claims`` function.

    The Yivi implementation of ``before_process_claims`` checks the claims and updates
    the config to make sure the correct loa configuration is used. Because Yivi has loa
    config for bsn and kvk, we need to define the default loa dynamically based on the
    received claims.
    """

    @mock_yivi_config(
        bsn_claim=["test.attribute.bsn"],
        bsn_loa_claim=["test.attribute.loa.bsn"],
        bsn_default_loa="urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard",
        bsn_loa_value_mapping={"mapping bsn": "schema definition"},
    )
    def test_before_process_claims_with_bsn_loa_config(self):
        config = YiviOpenIDConnectConfig.get_solo()
        plugin.before_process_claims(
            config,
            {
                "test.attribute.bsn": "123456789",
                "test.attribute.loa.bsn": "urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI",
            },
        )

        # When, for some reason, both bsn and kvk claims are received, we treat bsn as
        # identification.
        self.assertEqual(config.loa_claim, ["test.attribute.loa.bsn"])
        self.assertEqual(
            config.default_loa, "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard"
        )
        self.assertEqual(config.loa_value_mapping, {"mapping bsn": "schema definition"})

    @mock_yivi_config(
        kvk_claim=["test.attribute.kvk"],
        kvk_loa_claim=["test.attribute.loa.kvk"],
        kvk_default_loa="urn:etoegang:core:assurance-class:loa2",
        kvk_loa_value_mapping={"mapping kvk": "schema definition"},
    )
    def test_before_process_claims_with_kvk_loa_config(self):
        config = YiviOpenIDConnectConfig.get_solo()
        plugin.before_process_claims(
            config,
            {
                "test.attribute.kvk": "12345678",
                "test.attribute.loa.kvk": "urn:etoegang:core:assurance-class:loa3",
            },
        )

        # When, for some reason, both bsn and kvk claims are received, we treat bsn as
        # identification.
        self.assertEqual(config.loa_claim, ["test.attribute.loa.kvk"])
        self.assertEqual(config.default_loa, "urn:etoegang:core:assurance-class:loa2")
        self.assertEqual(config.loa_value_mapping, {"mapping kvk": "schema definition"})

    @mock_yivi_config(
        bsn_claim=["test.attribute.bsn"],
        bsn_loa_claim=["test.attribute.loa.bsn"],
        bsn_default_loa="urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard",
        bsn_loa_value_mapping={"mapping bsn": "schema definition"},
        kvk_claim=["test.attribute.kvk"],
        kvk_loa_claim=["test.attribute.loa.kvk"],
        kvk_default_loa="urn:etoegang:core:assurance-class:loa2",
        kvk_loa_value_mapping={"mapping kvk": "schema definition"},
    )
    def test_before_process_claims_with_bsn_and_kvk_loa_config(self):
        config = YiviOpenIDConnectConfig.get_solo()
        plugin.before_process_claims(
            config,
            {
                "test.attribute.bsn": "123456789",
                "test.attribute.loa.bsn": "urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI",
                "test.attribute.kvk": "12345678",
                "test.attribute.loa.kvk": "urn:etoegang:core:assurance-class:loa3",
            },
        )

        # When, for some reason, both bsn and kvk claims are received, we treat bsn as
        # the primary identification.
        self.assertEqual(config.loa_claim, ["test.attribute.loa.bsn"])
        self.assertEqual(
            config.default_loa, "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard"
        )
        self.assertEqual(config.loa_value_mapping, {"mapping bsn": "schema definition"})

    @mock_yivi_config()
    def test_before_process_claims_without_bsn_and_kvk_loa_config(self):
        config = YiviOpenIDConnectConfig.get_solo()
        plugin.before_process_claims(config, {})

        # When, for some reason, both bsn and kvk claims are received, we treat bsn as
        # identification.
        self.assertEqual(config.loa_claim, [""])
        self.assertEqual(config.default_loa, None)
        self.assertEqual(config.loa_value_mapping, None)


class YiviPluginExtractAdditionalClaimsTest(TestCase):
    """
    Testing the Yivi plugin ``extract_additional_claims`` function.
    """

    def test_extract_additional_claims_with_known_attributes(self):
        AttributeGroupFactory(
            name="know_attributes", attributes=["firstname", "lastname"]
        )
        AttributeGroupFactory(name="know_attributes_2", attributes=["dob"])
        plugin_options: YiviOptions = {
            "authentication_options": [],
            "additional_attributes_groups": ["know_attributes", "know_attributes_2"],
            "bsn_loa": "",
            "kvk_loa": "",
        }
        data = {"firstname": "bob", "lastname": "joe", "dob": "21-01-1999"}

        extracted_claims = plugin.extract_additional_claims(plugin_options, data)
        self.assertEqual(
            extracted_claims,
            {"firstname": "bob", "lastname": "joe", "dob": "21-01-1999"},
        )

    def test_extract_additional_claims_with_unknown_attributes(self):
        plugin_options: YiviOptions = {
            "authentication_options": [],
            "additional_attributes_groups": ["unknow_attributes"],
            "bsn_loa": "",
            "kvk_loa": "",
        }
        data = {"firstname": "bob"}

        extracted_claims = plugin.extract_additional_claims(plugin_options, data)
        self.assertEqual(extracted_claims, {})

    def test_extract_additional_claims_with_missing_claims(self):
        AttributeGroupFactory(
            name="know_attributes", attributes=["firstname", "lastname"]
        )
        plugin_options: YiviOptions = {
            "authentication_options": [],
            "additional_attributes_groups": ["know_attributes"],
            "bsn_loa": "",
            "kvk_loa": "",
        }
        data = {"firstname": "bob"}

        extracted_claims = plugin.extract_additional_claims(plugin_options, data)
        self.assertEqual(extracted_claims, {"firstname": "bob"})


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


class YiviPluginSensitiveClaimsTest(TestCase):
    """
    Testing the Yivi plugin ``get_sensitive_claims`` function.

    All Yivi additional attributes (configured in the FormAuthenticationBackend) should
    be marked as sensitive. This is because we cannot know what information will be
    requested using Yivi (as the admins/municipalities decide this).
    """

    def test_all_configured_additional_attributes_are_present_in_the_get_sensitive_claims(
        self,
    ):
        AttributeGroupFactory(
            name="know_attributes", attributes=["firstname", "lastname"]
        )
        AttributeGroupFactory(name="know_attributes_2", attributes=["dob"])

        plugin_options: YiviOptions = {
            "authentication_options": [],
            "additional_attributes_groups": ["know_attributes", "know_attributes_2"],
            "bsn_loa": "",
            "kvk_loa": "",
        }

        claims = {
            "firstname": "John",
            "lastname": "Doe",
            "dob": "01-01-2000",
            "random_attribute": "random value",
        }

        sensitive_claims = plugin.get_sensitive_claims(plugin_options, claims=claims)
        self.assertEqual(
            sensitive_claims,
            ["firstname", "lastname", "dob"],
        )
