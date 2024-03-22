from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from digid_eherkenning.models import DigidConfiguration, EherkenningConfiguration
from privates.test import temp_private_root
from simple_certmanager.test.factories import CertificateFactory

from openforms.config.constants import CSPDirective
from openforms.config.models import CSPSetting
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.utils.tests.cache import clear_caches

TEST_FILES = Path(__file__).parent / "data"
DIGID_METADATA_POST = TEST_FILES / "metadata_POST_bindings.xml"
EHERKENNING_METADATA_POST = TEST_FILES / "eherkenning-metadata.xml"


@temp_private_root()
@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class DigidCSPUpdateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cert = CertificateFactory.create(label="DigiD", with_private_key=True)

        cls.config = DigidConfiguration.get_solo()

        cls.config.certificate = cert
        cls.config.idp_service_entity_id = "https://test-digid.nl"
        cls.config.want_assertions_signed = False
        cls.config.entity_id = "https://test-sp.nl"
        cls.config.base_url = "https://test-sp.nl"
        cls.config.service_name = "Test"
        cls.config.service_description = "Test description"
        cls.config.slo = False
        cls.config.save()

    def setUp(self):
        super().setUp()

        clear_caches()
        self.addCleanup(clear_caches)

    @patch(
        "onelogin.saml2.idp_metadata_parser.OneLogin_Saml2_IdPMetadataParser.get_metadata"
    )
    def test_csp_updates_for_digid(self, get_metadata):
        # assert no csp entries exist with initial solo model
        self.assertTrue(CSPSetting.objects.none)

        # assert new csp entry is added after adding metadata url
        metadata_content = DIGID_METADATA_POST.read_text("utf-8")
        get_metadata.return_value = metadata_content
        self.config.metadata_file_source = "https://test-digid.nl"
        self.config.save()

        csp_added = CSPSetting.objects.get()

        self.assertEqual(csp_added.content_object, self.config)
        self.assertEqual(csp_added.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(
            csp_added.value,
            "https://test-digid.nl/saml/idp/request_authentication "
            "https://test-digid.nl/saml/idp/request_logout "
            "https://digid.nl "
            "https://*.digid.nl",
        )

        # assert new csp entry is added and the old one is deleted after url update
        self.config.metadata_file_source = "https://test-digid-post-bindings.nl"
        self.config.save()

        csp_updated = CSPSetting.objects.get()

        self.assertEqual(get_metadata.call_count, 2)
        self.assertFalse(CSPSetting.objects.filter(id=csp_added.id))
        self.assertEqual(csp_updated.content_object, self.config)
        self.assertEqual(csp_updated.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(
            csp_updated.value,
            "https://test-digid.nl/saml/idp/request_authentication "
            "https://test-digid.nl/saml/idp/request_logout "
            "https://digid.nl "
            "https://*.digid.nl",
        )

    @patch(
        "onelogin.saml2.idp_metadata_parser.OneLogin_Saml2_IdPMetadataParser.get_metadata"
    )
    @override_settings(CSP_FORM_ACTION=["'self'"])
    def test_response_headers_contain_form_action_values_in_digid(self, get_metadata):
        form = FormFactory.create(authentication_backends=["digid"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        metadata_content = DIGID_METADATA_POST.read_text("utf-8")
        get_metadata.return_value = metadata_content
        self.config.metadata_file_source = "https://test-digid.nl"
        self.config.save()

        login_url = reverse(
            "authentication:start", kwargs={"slug": form.slug, "plugin_id": "digid"}
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"http://testserver{form_path}?_start=1"

        # redirect_to_digid_login
        response = self.client.get(login_url, {"next": form_url}, follow=True)

        self.assertEqual(get_metadata.call_count, 1)
        self.assertIn(
            "form-action "
            "'self' "
            "https://test-digid.nl/saml/idp/request_authentication "
            "https://test-digid.nl/saml/idp/request_logout "
            "https://digid.nl "
            "https://*.digid.nl;",
            response.headers["Content-Security-Policy"],
        )


@temp_private_root()
class EherkenningCSPUpdateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cert = CertificateFactory.create(label="eHerkenning", with_private_key=True)

        cls.config = EherkenningConfiguration.get_solo()

        cls.config.certificate = cert
        cls.config.idp_service_entity_id = (
            "urn:etoegang:DV:00000001111111111000:entities:9000"
        )
        cls.config.want_assertions_signed = False
        cls.config.entity_id = "https://test-sp.nl"
        cls.config.base_url = "https://test-sp.nl"
        cls.config.service_name = "Test"
        cls.config.service_description = "Test"
        cls.config.eh_loa = "urn:etoegang:core:assurance-class:loa3"
        cls.config.oin = "00000001111111111000"
        cls.config.no_eidas = True
        cls.config.privacy_policy = "https://test-sp.nl/privacy_policy"
        cls.config.makelaar_id = "00000002222222222000"
        cls.config.organization_name = "Test Organisation"
        cls.config.save()

    def setUp(self):
        super().setUp()

        clear_caches()
        self.addCleanup(clear_caches)

    @patch(
        "onelogin.saml2.idp_metadata_parser.OneLogin_Saml2_IdPMetadataParser.get_metadata"
    )
    def test_csp_updates_for_eherkenning(self, get_metadata):
        # assert no csp entries exist with initial solo model
        self.assertTrue(CSPSetting.objects.none)

        # assert new csp entry is added after adding metadata url

        metadata_content = EHERKENNING_METADATA_POST.read_text("utf-8")
        get_metadata.return_value = metadata_content
        self.config.metadata_file_source = "https://test-sp.nl"
        self.config.save()

        csp_added = CSPSetting.objects.get()

        self.assertEqual(csp_added.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(
            csp_added.value,
            "https://test-iwelcome.nl/broker/sso/1.13 "
            "https://ehm01.iwelcome.nl/broker/slo/1.13 "
            "https://*.eherkenning.nl",
        )

        # assert new csp entry is added and old one is deleted after url update
        self.config.metadata_file_source = "https://updated-test-sp.nl"
        self.config.save()

        csp_updated = CSPSetting.objects.get()

        self.assertEqual(get_metadata.call_count, 2)
        self.assertFalse(CSPSetting.objects.filter(id=csp_added.id))
        self.assertEqual(csp_added.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(
            csp_updated.value,
            "https://test-iwelcome.nl/broker/sso/1.13 "
            "https://ehm01.iwelcome.nl/broker/slo/1.13 "
            "https://*.eherkenning.nl",
        )

    @patch(
        "onelogin.saml2.idp_metadata_parser.OneLogin_Saml2_IdPMetadataParser.get_metadata"
    )
    @override_settings(CSP_FORM_ACTION=["'self'"])
    def test_response_headers_contain_form_action_values_in_eherkenning(
        self, get_metadata
    ):
        form = FormFactory.create(
            authentication_backends=["eherkenning"],
            generate_minimal_setup=True,
            formstep__form_definition__login_required=True,
        )
        metadata_content = EHERKENNING_METADATA_POST.read_text("utf-8")
        get_metadata.return_value = metadata_content
        self.config.metadata_file_source = (
            "urn:etoegang:DV:00000001111111111000:entities:9000"
        )
        self.config.save()

        login_url = reverse(
            "authentication:start",
            kwargs={"slug": form.slug, "plugin_id": "eherkenning"},
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"http://testserver{form_path}"

        # redirect_to_eherkenning_login
        response = self.client.get(login_url, {"next": form_url}, follow=True)

        self.assertEqual(get_metadata.call_count, 1)
        self.assertIn(
            "form-action "
            "'self' "
            "https://test-iwelcome.nl/broker/sso/1.13 "
            "https://ehm01.iwelcome.nl/broker/slo/1.13 "
            "https://*.eherkenning.nl;",
            response.headers["Content-Security-Policy"],
        )
