from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from mozilla_django_oidc_db.models import OIDCClient
from mozilla_django_oidc_db.registry import register as registry
from mozilla_django_oidc_db.views import (
    _RETURN_URL_SESSION_KEY,
)

from openforms.authentication.contrib.digid_eherkenning_oidc.oidc_plugins.types import (
    ClaimProcessingInstructions,
)
from openforms.forms.tests.factories import FormFactory
from openforms.utils.tests.keycloak import mock_get_random_string, mock_oidc_client

from .....tests.factories import AttributeGroupFactory
from .....tests.utils import URLsHelper
from ...config import YiviOptions
from ...constants import PLUGIN_ID as YIVI_PLUGIN_ID
from ...oidc_plugins.constants import OIDC_YIVI_IDENTIFIER


class ProcessClaimsYiviTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.plugin = registry[OIDC_YIVI_IDENTIFIER]

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

    @mock_oidc_client(
        OIDC_YIVI_IDENTIFIER,
        overrides={
            "options.identity_settings.bsn_claim_path": ["test.attribute.bsn"],
            "options.identity_settings.bsn_loa_claim_path": ["bsn.loa"],
        },
    )
    def test_yivi_process_claims_with_dots_in_path(self):
        AttributeGroupFactory(
            name="know_attributes",
            attributes=["irma-demo.gemeente.personalData.familyname"],
        )
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

        additional_attributes = self.plugin.get_additional_attributes(request)
        processed_claims = self.plugin.process_claims(
            {
                "test.attribute.bsn": "123456782",
                "bsn.loa": "low",
                "irma-demo.gemeente.personalData.familyname": "Doe",
            },
            additional_attributes,
        )

        self.assertEqual(
            processed_claims,
            {
                "bsn_claim": "123456782",
                "loa_claim": "low",
                "additional_claims": {
                    "irma-demo.gemeente.personalData.familyname": "Doe"
                },
            },
        )

    @mock_oidc_client(
        OIDC_YIVI_IDENTIFIER,
        overrides={
            "options.identity_settings.bsn_claim_path": ["test.attribute.bsn"],
        },
    )
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

        additional_attributes = self.plugin.get_additional_attributes(request)
        extracted_claims = self.plugin.process_claims(
            {"firstname": "bob", "lastname": "joe", "dob": "21-01-1999"},
            additional_attributes,
        )
        self.assertEqual(
            extracted_claims,
            {
                "additional_claims": {
                    "firstname": "bob",
                    "lastname": "joe",
                    "dob": "21-01-1999",
                }
            },
        )

    @mock_oidc_client(
        OIDC_YIVI_IDENTIFIER,
        overrides={
            "options.identity_settings.bsn_claim_path": ["test.attribute.bsn"],
        },
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

        additional_attributes = self.plugin.get_additional_attributes(request)
        extracted_claims = self.plugin.process_claims(
            {"firstname": "bob"}, additional_attributes
        )

        self.assertEqual(extracted_claims, {})

    @mock_oidc_client(
        OIDC_YIVI_IDENTIFIER,
        overrides={
            "options.identity_settings.bsn_claim_path": ["test.attribute.bsn"],
        },
    )
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

        additional_attributes = self.plugin.get_additional_attributes(request)
        extracted_claims = self.plugin.process_claims(
            {"firstname": "bob"}, additional_attributes
        )

        self.assertEqual(extracted_claims, {"additional_claims": {"firstname": "bob"}})

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

        additional_attributes = self.plugin.get_additional_attributes(request)
        sensitive_claims = self.plugin.get_sensitive_claims(additional_attributes)

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


class YiviPluginProcessClaimsTest(TestCase):
    """
    Testing the Yivi plugin ``before_process_claims`` function.

    The Yivi implementation of ``before_process_claims`` checks the claims and updates
    the config to make sure the correct loa configuration is used. Because Yivi has loa
    config for bsn and kvk, we need to define the default loa dynamically based on the
    received claims.
    """

    def _setup_form(self) -> HttpRequest:
        form = FormFactory.create(
            authentication_backend=YIVI_PLUGIN_ID,
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
        oidc_plugin = registry[OIDC_YIVI_IDENTIFIER]
        config = OIDCClient.objects.get(identifier=OIDC_YIVI_IDENTIFIER)
        request = self._setup_form()

        additional_attributes = oidc_plugin.get_additional_attributes(request)
        claim_processing_instructions: ClaimProcessingInstructions = oidc_plugin.get_claim_processing_instructions(
            {
                "test.attribute.bsn": "123456789",
                "test.attribute.loa.bsn": "urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI",
            },
            config,
            additional_attributes,
        )

        # When, for some reason, both bsn and kvk claims are received, we treat bsn as
        # identification.
        self.assertEqual(
            claim_processing_instructions["loa_claims"]["path_in_claim"],
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
        oidc_plugin = registry[OIDC_YIVI_IDENTIFIER]
        config = OIDCClient.objects.get(identifier=OIDC_YIVI_IDENTIFIER)
        request = self._setup_form()

        additional_attributes = oidc_plugin.get_additional_attributes(request)
        claim_processing_instructions = oidc_plugin.get_claim_processing_instructions(
            {
                "test.attribute.kvk": "12345678",
                "test.attribute.loa.kvk": "urn:etoegang:core:assurance-class:loa3",
            },
            config,
            additional_attributes,
        )

        # When, for some reason, both bsn and kvk claims are received, we treat bsn as
        # identification.
        self.assertEqual(
            claim_processing_instructions["loa_claims"]["path_in_claim"],
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
        oidc_plugin = registry[OIDC_YIVI_IDENTIFIER]
        config = OIDCClient.objects.get(identifier=OIDC_YIVI_IDENTIFIER)
        request = self._setup_form()

        additional_attributes = oidc_plugin.get_additional_attributes(request)
        claim_processing_instructions = oidc_plugin.get_claim_processing_instructions(
            {
                "test.attribute.bsn": "123456789",
                "test.attribute.loa.bsn": "urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI",
                "test.attribute.kvk": "12345678",
                "test.attribute.loa.kvk": "urn:etoegang:core:assurance-class:loa3",
            },
            config,
            additional_attributes,
        )

        # When, for some reason, both bsn and kvk claims are received, we treat bsn as
        # the primary identification.
        self.assertEqual(
            claim_processing_instructions["loa_claims"]["path_in_claim"],
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
        oidc_plugin = registry[OIDC_YIVI_IDENTIFIER]
        config = OIDCClient.objects.get(identifier=OIDC_YIVI_IDENTIFIER)
        request = self._setup_form()

        additional_attributes = oidc_plugin.get_additional_attributes(request)
        claim_processing_instructions = oidc_plugin.get_claim_processing_instructions(
            {}, config, additional_attributes
        )

        # When, for some reason, both bsn and kvk claims are received, we treat bsn as
        # identification.
        self.assertEqual(
            claim_processing_instructions["loa_claims"]["path_in_claim"], []
        )
        self.assertEqual(claim_processing_instructions["loa_claims"]["default"], "")
        self.assertEqual(
            claim_processing_instructions["loa_claims"]["value_mapping"], []
        )
