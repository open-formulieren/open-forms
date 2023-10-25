from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from digid_eherkenning.models.digid import DigidConfiguration
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
METADATA_POST = TEST_FILES / "metadata_POST_bindings.xml"


@temp_private_root()
@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class CSPUpdateTests(TestCase):
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
    def test_csp_updates(self, get_metadata):
        # assert no csp entries exist with initial solo model
        self.assertTrue(CSPSetting.objects.none)

        # assert new csp entry is added after adding metadata url
        with METADATA_POST.open("rb") as md_file:
            metadata_content = md_file.read().decode("utf-8")
            get_metadata.return_value = metadata_content
            self.config.metadata_file_source = "https://test-digid.nl"
            self.config.save()

        csp_added = CSPSetting.objects.get()

        self.assertEqual(csp_added.content_object, self.config)
        self.assertEqual(csp_added.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(
            csp_added.value,
            "https://digid.nl "
            "https://*.digid.nl "
            "https://test-digid.nl/saml/idp/request_authentication "
            "https://test-digid.nl/saml/idp/request_logout",
        )

        # assert new csp entry is added and the old one is deleted after url update
        self.config.metadata_file_source = "https://test-digid-post-bindings.nl"
        self.config.save()

        csp_updated = CSPSetting.objects.get()

        self.assertFalse(CSPSetting.objects.filter(id=csp_added.id))
        self.assertEqual(csp_updated.content_object, self.config)
        self.assertEqual(csp_updated.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(
            csp_updated.value,
            "https://digid.nl "
            "https://*.digid.nl "
            "https://test-digid.nl/saml/idp/request_authentication "
            "https://test-digid.nl/saml/idp/request_logout",
        )

    @patch(
        "onelogin.saml2.idp_metadata_parser.OneLogin_Saml2_IdPMetadataParser.get_metadata"
    )
    def test_response_headers_contain_form_action_values(self, get_metadata):
        form = FormFactory.create(authentication_backends=["digid"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        with METADATA_POST.open("rb") as md_file:
            metadata_content = md_file.read().decode("utf-8")
            get_metadata.return_value = metadata_content
            self.config.metadata_file_source = "https://test-digid.nl"
            self.config.save()

        login_url = reverse(
            "authentication:start", kwargs={"slug": form.slug, "plugin_id": "digid"}
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"http://testserver{form_path}?_start=1"

        # redirect_to_digid_login
        response = self.client.get(f"{login_url}?next={form_url}", follow=True)

        self.assertIn(
            "form-action "
            "'self' "
            "https://digid.nl "
            "https://*.digid.nl "
            "https://test-digid.nl/saml/idp/request_authentication "
            "https://test-digid.nl/saml/idp/request_logout;",
            response.headers["Content-Security-Policy"],
        )
