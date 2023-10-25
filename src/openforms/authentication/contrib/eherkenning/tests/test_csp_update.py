from pathlib import Path
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from digid_eherkenning.models.eherkenning import EherkenningConfiguration
from privates.test import temp_private_root
from simple_certmanager.test.factories import CertificateFactory

from openforms.config.constants import CSPDirective
from openforms.config.models import CSPSetting
from openforms.forms.tests.factories import FormFactory
from openforms.utils.tests.cache import clear_caches

TEST_FILES = Path(__file__).parent / "data"
METADATA = TEST_FILES / "eherkenning-metadata.xml"


@temp_private_root()
class CSPUpdateTests(TestCase):
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
        cls.config.loa = "urn:etoegang:core:assurance-class:loa3"
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
    def test_csp_updates(self, get_metadata):
        # assert no csp entries exist with initial solo model
        self.assertTrue(CSPSetting.objects.none)

        # assert new csp entry is added after adding metadata url
        with METADATA.open("rb") as md_file:
            metadata_content = md_file.read().decode("utf-8")
            get_metadata.return_value = metadata_content
            self.config.metadata_file_source = "https://test-sp.nl"
            self.config.save()

        csp_added = CSPSetting.objects.get()

        self.assertEqual(csp_added.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(
            csp_added.value,
            "https://test-iwelcome.nl/broker/sso/1.13 "
            "https://ehm01.iwelcome.nl/broker/slo/1.13",
        )

        # assert new csp entry is added and old one is deleted after url update
        self.config.metadata_file_source = "https://updated-test-sp.nl"
        self.config.save()

        csp_updated = CSPSetting.objects.get()

        self.assertFalse(CSPSetting.objects.filter(id=csp_added.id))
        self.assertEqual(csp_added.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(
            csp_updated.value,
            "https://test-iwelcome.nl/broker/sso/1.13 "
            "https://ehm01.iwelcome.nl/broker/slo/1.13",
        )

    @patch(
        "onelogin.saml2.idp_metadata_parser.OneLogin_Saml2_IdPMetadataParser.get_metadata"
    )
    def test_response_headers_contain_form_action_values(self, get_metadata):
        form = FormFactory.create(
            authentication_backends=["eherkenning"],
            generate_minimal_setup=True,
            formstep__form_definition__login_required=True,
        )
        with METADATA.open("rb") as md_file:
            metadata_content = md_file.read().decode("utf-8")
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

        self.assertIn(
            "form-action "
            "'self' "
            "https://test-iwelcome.nl/broker/sso/1.13 "
            "https://ehm01.iwelcome.nl/broker/slo/1.13;",
            response.headers["Content-Security-Policy"],
        )
