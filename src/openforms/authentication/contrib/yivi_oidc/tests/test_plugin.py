from django.http import HttpRequest
from django.test import TestCase
from django.test.client import RequestFactory

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels
from mozilla_django_oidc_db.models import OIDCClient
from mozilla_django_oidc_db.registry import register as oidc_registry
from mozilla_django_oidc_db.views import (
    _RETURN_URL_SESSION_KEY,
)

from openforms.authentication.constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.authentication.contrib.digid_eherkenning_oidc.oidc_plugins.types import (
    ClaimProcessingInstructions,
)
from openforms.authentication.contrib.yivi_oidc.config import YiviOptions
from openforms.authentication.contrib.yivi_oidc.oidc_plugins.constants import (
    OIDC_YIVI_IDENTIFIER,
)
from openforms.authentication.registry import register
from openforms.authentication.tests.factories import (
    AttributeGroupFactory,
)
from openforms.forms.tests.factories import FormFactory
from openforms.utils.tests.keycloak import mock_get_random_string, mock_oidc_client

from ....tests.utils import URLsHelper
from ..constants import PLUGIN_ID as YIVI_PLUGIN_ID

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


class YiviPluginProcessClaimsTest(TestCase):
    """
    Testing the Yivi plugin ``before_process_claims`` function.

    The Yivi implementation of ``before_process_claims`` checks the claims and updates
    the config to make sure the correct loa configuration is used. Because Yivi has loa
    config for bsn and kvk, we need to define the default loa dynamically based on the
    received claims.
    """

    @mock_get_random_string()
    @mock_oidc_client(
        OIDC_YIVI_IDENTIFIER,
        overrides={
            "options.identity_settings.bsn_claim_path": ["test.attribute.bsn"],
            "options.identity_settings.bsn_loa_claim_path": ["test.attribute.loa.bsn"],
            "options.identity_settings.bsn_default_loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard",
            "options.identity_settings.bsn_loa_value_mapping": [
                {"from": "bsn", "to": "bla"}
            ],
        },
    )
    def test_before_process_claims_with_bsn_loa_config(self):
        oidc_plugin = oidc_registry[OIDC_YIVI_IDENTIFIER]
        config = OIDCClient.objects.get(identifier=OIDC_YIVI_IDENTIFIER)

        factory = RequestFactory()
        factory = factory
        request = factory.get("/irrelevant")

        claim_processing_instructions: ClaimProcessingInstructions = oidc_plugin.get_claim_processing_instructions(
            request,
            {
                "test.attribute.bsn": "123456789",
                "test.attribute.loa.bsn": "urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI",
            },
            config,
        )

        # When, for some reason, both bsn and kvk claims are received, we treat bsn as
        # identification.
        self.assertEqual(
            claim_processing_instructions["loa_claims"]["claim_path"],
            ["test.attribute.loa.bsn"],
        )
        self.assertEqual(
            claim_processing_instructions["loa_claims"]["default"],
            "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard",
        )
        self.assertEqual(
            claim_processing_instructions["loa_claims"]["value_mapping"],
            [{"from": "bsn", "to": "bla"}],
        )

    @mock_get_random_string()
    @mock_oidc_client(
        OIDC_YIVI_IDENTIFIER,
        overrides={
            "options.identity_settings.kvk_claim_path": ["test.attribute.kvk"],
            "options.identity_settings.kvk_loa_claim_path": ["test.attribute.loa.kvk"],
            "options.identity_settings.kvk_default_loa": "urn:etoegang:core:assurance-class:loa2",
            "options.identity_settings.kvk_loa_value_mapping": [
                {"from": "kvk", "to": "bla"}
            ],
        },
    )
    def test_before_process_claims_with_kvk_loa_config(self):
        oidc_plugin = oidc_registry[OIDC_YIVI_IDENTIFIER]
        config = OIDCClient.objects.get(identifier=OIDC_YIVI_IDENTIFIER)

        factory = RequestFactory()
        factory = factory
        request = factory.get("/irrelevant")

        claim_processing_instructions = oidc_plugin.get_claim_processing_instructions(
            request,
            {
                "test.attribute.kvk": "12345678",
                "test.attribute.loa.kvk": "urn:etoegang:core:assurance-class:loa3",
            },
            config,
        )

        # When, for some reason, both bsn and kvk claims are received, we treat bsn as
        # identification.
        self.assertEqual(
            claim_processing_instructions["loa_claims"]["claim_path"],
            ["test.attribute.loa.kvk"],
        )
        self.assertEqual(
            claim_processing_instructions["loa_claims"]["default"],
            "urn:etoegang:core:assurance-class:loa2",
        )
        self.assertEqual(
            claim_processing_instructions["loa_claims"]["value_mapping"],
            [{"from": "kvk", "to": "bla"}],
        )

    @mock_get_random_string()
    @mock_oidc_client(
        OIDC_YIVI_IDENTIFIER,
        overrides={
            "options.identity_settings.bsn_claim_path": ["test.attribute.bsn"],
            "options.identity_settings.bsn_loa_claim_path": ["test.attribute.loa.bsn"],
            "options.identity_settings.bsn_default_loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard",
            "options.identity_settings.bsn_loa_value_mapping": [
                {"from": "bsn", "to": "bla"}
            ],
            "options.identity_settings.kvk_claim_path": ["test.attribute.kvk"],
            "options.identity_settings.kvk_loa_claim_path": ["test.attribute.loa.kvk"],
            "options.identity_settings.kvk_default_loa": "urn:etoegang:core:assurance-class:loa2",
            "options.identity_settings.kvk_loa_value_mapping": [
                {"from": "kvk", "to": "bla"}
            ],
        },
    )
    def test_before_process_claims_with_bsn_and_kvk_loa_config(self):
        oidc_plugin = oidc_registry[OIDC_YIVI_IDENTIFIER]
        config = OIDCClient.objects.get(identifier=OIDC_YIVI_IDENTIFIER)

        factory = RequestFactory()
        factory = factory
        request = factory.get("/irrelevant")

        claim_processing_instructions = oidc_plugin.get_claim_processing_instructions(
            request,
            {
                "test.attribute.bsn": "123456789",
                "test.attribute.loa.bsn": "urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI",
                "test.attribute.kvk": "12345678",
                "test.attribute.loa.kvk": "urn:etoegang:core:assurance-class:loa3",
            },
            config,
        )

        # When, for some reason, both bsn and kvk claims are received, we treat bsn as
        # the primary identification.
        self.assertEqual(
            claim_processing_instructions["loa_claims"]["claim_path"],
            ["test.attribute.loa.bsn"],
        )
        self.assertEqual(
            claim_processing_instructions["loa_claims"]["default"],
            "urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard",
        )
        self.assertEqual(
            claim_processing_instructions["loa_claims"]["value_mapping"],
            [{"from": "bsn", "to": "bla"}],
        )

    @mock_get_random_string()
    @mock_oidc_client(OIDC_YIVI_IDENTIFIER)
    def test_before_process_claims_without_bsn_and_kvk_loa_config(self):
        oidc_plugin = oidc_registry[OIDC_YIVI_IDENTIFIER]
        config = OIDCClient.objects.get(identifier=OIDC_YIVI_IDENTIFIER)

        factory = RequestFactory()
        factory = factory
        request = factory.get("/irrelevant")

        claim_processing_instructions = oidc_plugin.get_claim_processing_instructions(
            request, {}, config
        )

        # When, for some reason, both bsn and kvk claims are received, we treat bsn as
        # identification.
        self.assertEqual(claim_processing_instructions["loa_claims"]["claim_path"], [])
        self.assertEqual(claim_processing_instructions["loa_claims"]["default"], "")
        self.assertEqual(
            claim_processing_instructions["loa_claims"]["value_mapping"], []
        )


class YiviPluginExtractAdditionalClaimsTest(TestCase):
    """
    Testing the Yivi plugin ``extract_additional_claims`` function.
    """

    def _setup_form(self, options: YiviOptions) -> HttpRequest:
        form = FormFactory.create(
            authentication_backend=YIVI_PLUGIN_ID,
            authentication_backend__options=options,
        )
        url_helper = URLsHelper(form=form)

        session = self.client.session
        session[_RETURN_URL_SESSION_KEY] = url_helper.get_auth_start(
            plugin_id=YIVI_PLUGIN_ID
        )
        session.save()

        factory = RequestFactory()
        factory = factory
        request = factory.get("/irrelevant")
        request.session = session

        return request

    def test_extract_additional_claims_with_known_attributes(self):
        AttributeGroupFactory(
            name="know_attributes", attributes=["firstname", "lastname"]
        )
        AttributeGroupFactory(name="know_attributes_2", attributes=["dob"])
        request = self._setup_form(
            options={
                "authentication_options": [],
                "additional_attributes_groups": [
                    "know_attributes",
                    "know_attributes_2",
                ],
                "bsn_loa": "",
                "kvk_loa": "",
            }
        )

        oidc_plugin = oidc_registry[OIDC_YIVI_IDENTIFIER]

        extracted_claims = oidc_plugin.extract_additional_claims(
            request, {"firstname": "bob", "lastname": "joe", "dob": "21-01-1999"}
        )
        self.assertEqual(
            extracted_claims,
            {"firstname": "bob", "lastname": "joe", "dob": "21-01-1999"},
        )

    def test_extract_additional_claims_with_unknown_attributes(self):
        request = self._setup_form(
            options={
                "authentication_options": [],
                "additional_attributes_groups": ["unknow_attributes"],
                "bsn_loa": "",
                "kvk_loa": "",
            }
        )

        oidc_plugin = oidc_registry[OIDC_YIVI_IDENTIFIER]

        extracted_claims = oidc_plugin.extract_additional_claims(
            request, {"firstname": "bob"}
        )

        self.assertEqual(extracted_claims, {})

    def test_extract_additional_claims_with_missing_claims(self):
        AttributeGroupFactory(
            name="know_attributes", attributes=["firstname", "lastname"]
        )
        request = self._setup_form(
            options={
                "authentication_options": [],
                "additional_attributes_groups": ["know_attributes"],
                "bsn_loa": "",
                "kvk_loa": "",
            }
        )
        oidc_plugin = oidc_registry[OIDC_YIVI_IDENTIFIER]

        extracted_claims = oidc_plugin.extract_additional_claims(
            request, {"firstname": "bob"}
        )

        self.assertEqual(extracted_claims, {"firstname": "bob"})

    @mock_get_random_string()
    @mock_oidc_client(
        OIDC_YIVI_IDENTIFIER,
        overrides={
            "options.identity_settings.bsn_claim_path": ["test.attribute.bsn"],
            "options.identity_settings.kvk_claim_path": ["test.attribute.kvk"],
            "options.identity_settings.pseudo_claim_path": ["test.attribute.pseudo"],
        },
    )
    def test_all_configured_additional_attributes_are_present_in_the_get_sensitive_claims(
        self,
    ):
        AttributeGroupFactory(
            name="know_attributes", attributes=["firstname", "lastname"]
        )
        AttributeGroupFactory(name="know_attributes_2", attributes=["dob"])
        request = self._setup_form(
            options={
                "authentication_options": [],
                "additional_attributes_groups": [
                    "know_attributes",
                    "know_attributes_2",
                ],
                "bsn_loa": "",
                "kvk_loa": "",
            }
        )

        yivi_oidc_plugin = oidc_registry[OIDC_YIVI_IDENTIFIER]

        sensitive_claims = yivi_oidc_plugin.get_sensitive_claims(request)

        self.assertEqual(
            sensitive_claims,
            [
                ["test.attribute.bsn"],
                ["test.attribute.kvk"],
                ["test.attribute.pseudo"],
                ["firstname"],
                ["lastname"],
                ["dob"],
            ],
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
