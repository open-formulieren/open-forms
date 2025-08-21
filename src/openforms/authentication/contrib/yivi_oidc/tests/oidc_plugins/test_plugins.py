from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from mozilla_django_oidc_db.registry import register as oidc_register
from mozilla_django_oidc_db.tests.mixins import OIDCMixin
from mozilla_django_oidc_db.views import _RETURN_URL_SESSION_KEY

from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.authentication.tests.utils import URLsHelper
from openforms.contrib.auth_oidc.tests.factories import OFOIDCClientFactory
from openforms.contrib.auth_oidc.typing import ClaimProcessingInstructions
from openforms.forms.tests.factories import FormFactory

from ...config import YiviOptions
from ...constants import PLUGIN_ID as YIVI_PLUGIN_ID


class ProcessClaimsYiviTest(OIDCMixin, TestCase):
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
        request = factory.get("/irrelevant")
        request.session = session

        return request

    def test_yivi_process_claims_with_dots_in_path(self):
        oidc_client = OFOIDCClientFactory.create(
            with_yivi=True,
            options__identity_settings__bsn_claim_path=["test.attribute.bsn"],
            options__loa_settings__bsn_loa_claim_path=["bsn.loa"],
        )
        plugin = oidc_register[oidc_client.identifier]
        AttributeGroupFactory.create(
            name="know_attributes",
            uuid="e4bfa861-3ac0-4b9a-90ff-1bdbb3a17e09",
            attributes=["irma-demo.gemeente.personalData.familyname"],
        )
        request = self._setup_form(
            options={
                "authentication_options": [],
                "additional_attributes_groups": [
                    # The attributegroup that was defined above
                    "e4bfa861-3ac0-4b9a-90ff-1bdbb3a17e09",
                ],
                "bsn_loa": "",
                "kvk_loa": "",
            }
        )

        additional_attributes = plugin.get_additional_attributes(request)
        processed_claims = plugin.process_claims(
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

    def test_extract_additional_claims_with_known_attributes(self):
        oidc_client = OFOIDCClientFactory.create(
            with_yivi=True,
            options__identity_settings__bsn_claim_path=["test.attribute.bsn"],
        )
        plugin = oidc_register[oidc_client.identifier]
        AttributeGroupFactory.create(
            name="know_attributes",
            uuid="e4bfa861-3ac0-4b9a-90ff-1bdbb3a17e09",
            attributes=["firstname", "lastname"],
        )
        AttributeGroupFactory.create(
            name="know_attributes_2",
            uuid="9eb88579-a6e5-4d06-b780-6edc0968e673",
            attributes=["dob"],
        )
        request = self._setup_form(
            options={
                "authentication_options": [],
                "additional_attributes_groups": [
                    # The two attributegroups from above
                    "e4bfa861-3ac0-4b9a-90ff-1bdbb3a17e09",
                    "9eb88579-a6e5-4d06-b780-6edc0968e673",
                ],
                "bsn_loa": "",
                "kvk_loa": "",
            }
        )

        additional_attributes = plugin.get_additional_attributes(request)
        extracted_claims = plugin.process_claims(
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

    def test_extract_additional_claims_with_unknown_attributes(self):
        oidc_client = OFOIDCClientFactory.create(
            with_yivi=True,
            options__identity_settings__bsn_claim_path=["test.attribute.bsn"],
        )
        plugin = oidc_register[oidc_client.identifier]
        request = self._setup_form(
            options={
                "authentication_options": [],
                "additional_attributes_groups": [
                    # An unknown attributegroup uuid
                    "9eb88579-a6e5-4d06-b780-6edc0968e673"
                ],
                "bsn_loa": "",
                "kvk_loa": "",
            }
        )

        additional_attributes = plugin.get_additional_attributes(request)
        extracted_claims = plugin.process_claims(
            {"firstname": "bob"}, additional_attributes
        )

        self.assertEqual(extracted_claims, {})

    def test_extract_additional_claims_with_missing_claims(self):
        oidc_client = OFOIDCClientFactory.create(
            with_yivi=True,
            options__identity_settings__bsn_claim_path=["test.attribute.bsn"],
        )
        plugin = oidc_register[oidc_client.identifier]
        AttributeGroupFactory.create(
            name="know_attributes",
            uuid="9eb88579-a6e5-4d06-b780-6edc0968e673",
            attributes=["firstname", "lastname"],
        )
        request = self._setup_form(
            options={
                "authentication_options": [],
                "additional_attributes_groups": [
                    "9eb88579-a6e5-4d06-b780-6edc0968e673"
                ],
                "bsn_loa": "",
                "kvk_loa": "",
            }
        )

        additional_attributes = plugin.get_additional_attributes(request)
        extracted_claims = plugin.process_claims(
            {"firstname": "bob"}, additional_attributes
        )

        self.assertEqual(extracted_claims, {"additional_claims": {"firstname": "bob"}})

    def test_all_configured_additional_attributes_are_present_in_the_get_sensitive_claims(
        self,
    ):
        oidc_client = OFOIDCClientFactory.create(
            with_yivi=True,
            options__identity_settings__bsn_claim_path=["test.attribute.bsn"],
            options__identity_settings__kvk_claim_path=["test.attribute.kvk"],
            options__identity_settings__pseudo_claim_path=["test.attribute.pseudo"],
        )

        plugin = oidc_register[oidc_client.identifier]
        AttributeGroupFactory.create(
            name="know_attributes",
            uuid="9eb88579-a6e5-4d06-b780-6edc0968e673",
            attributes=["firstname", "lastname"],
        )
        AttributeGroupFactory.create(
            name="know_attributes_2",
            uuid="e4bfa861-3ac0-4b9a-90ff-1bdbb3a17e09",
            attributes=["dob"],
        )
        request = self._setup_form(
            options={
                "authentication_options": [],
                "additional_attributes_groups": [
                    # The two attributegroups from above
                    "9eb88579-a6e5-4d06-b780-6edc0968e673",
                    "e4bfa861-3ac0-4b9a-90ff-1bdbb3a17e09",
                ],
                "bsn_loa": "",
                "kvk_loa": "",
            }
        )

        additional_attributes = plugin.get_additional_attributes(request)
        sensitive_claims = plugin.get_sensitive_claims(additional_attributes)

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


class YiviPluginProcessClaimsTest(OIDCMixin, TestCase):
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
        request = factory.get("/irrelevant")
        request.session = session

        return request

    def test_before_process_claims_with_bsn_loa_config(self):
        oidc_client = OFOIDCClientFactory.create(
            with_yivi=True,
            options__identity_settings__bsn_claim_path=["test.attribute.bsn"],
            options__loa_settings__bsn_loa_claim_path=["test.attribute.loa.bsn"],
            options__loa_settings__bsn_default_loa="urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard",
            options__loa_settings__bsn_loa_value_mapping=[{"from": "bsn", "to": "bla"}],
        )
        oidc_plugin = oidc_register[oidc_client.identifier]
        request = self._setup_form()

        additional_attributes = oidc_plugin.get_additional_attributes(request)
        claim_processing_instructions: ClaimProcessingInstructions = oidc_plugin.get_claim_processing_instructions(
            {
                "test.attribute.bsn": "123456789",
                "test.attribute.loa.bsn": "urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI",
            },
            oidc_client,
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

    def test_before_process_claims_with_kvk_loa_config(self):
        oidc_client = OFOIDCClientFactory.create(
            with_yivi=True,
            options__identity_settings__kvk_claim_path=["test.attribute.kvk"],
            options__loa_settings__kvk_loa_claim_path=["test.attribute.loa.kvk"],
            options__loa_settings__kvk_default_loa="urn:etoegang:core:assurance-class:loa2",
            options__loa_settings__kvk_loa_value_mapping=[{"from": "kvk", "to": "bla"}],
        )
        oidc_plugin = oidc_register[oidc_client.identifier]
        request = self._setup_form()

        additional_attributes = oidc_plugin.get_additional_attributes(request)
        claim_processing_instructions = oidc_plugin.get_claim_processing_instructions(
            {
                "test.attribute.kvk": "12345678",
                "test.attribute.loa.kvk": "urn:etoegang:core:assurance-class:loa3",
            },
            oidc_client,
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

    def test_before_process_claims_with_bsn_and_kvk_loa_config(self):
        oidc_client = OFOIDCClientFactory.create(
            with_yivi=True,
            options__identity_settings__bsn_claim_path=["test.attribute.bsn"],
            options__loa_settings__bsn_loa_claim_path=["test.attribute.loa.bsn"],
            options__loa_settings__bsn_default_loa="urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard",
            options__loa_settings__bsn_loa_value_mapping=[{"from": "bsn", "to": "bla"}],
            options__identity_settings__kvk_claim_path=["test.attribute.kvk"],
            options__loa_settings__kvk_loa_claim_path=["test.attribute.loa.kvk"],
            options__loa_settings__kvk_default_loa="urn:etoegang:core:assurance-class:loa2",
            options__loa_settings__kvk_loa_value_mapping=[{"from": "kvk", "to": "bla"}],
        )
        oidc_plugin = oidc_register[oidc_client.identifier]
        request = self._setup_form()

        additional_attributes = oidc_plugin.get_additional_attributes(request)
        claim_processing_instructions = oidc_plugin.get_claim_processing_instructions(
            {
                "test.attribute.bsn": "123456789",
                "test.attribute.loa.bsn": "urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI",
                "test.attribute.kvk": "12345678",
                "test.attribute.loa.kvk": "urn:etoegang:core:assurance-class:loa3",
            },
            oidc_client,
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

    def test_before_process_claims_without_bsn_and_kvk_loa_config(self):
        oidc_client = OFOIDCClientFactory.create(with_yivi=True)
        oidc_plugin = oidc_register[oidc_client.identifier]
        request = self._setup_form()

        additional_attributes = oidc_plugin.get_additional_attributes(request)
        claim_processing_instructions = oidc_plugin.get_claim_processing_instructions(
            {}, oidc_client, additional_attributes
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
