import os
from base64 import b64decode, b64encode
from hashlib import sha1
from unittest.mock import patch
from urllib.parse import urlencode

from django.conf import settings
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

from freezegun import freeze_time
from furl import furl
from lxml import etree
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from requests_mock import Mocker
from rest_framework import status

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)

EHERKENNING = {
    "base_url": "https://test-sp.nl",
    "entity_id": "urn:etoegang:DV:00000001111111111000:entities:9000",
    "service_entity_id": "urn:etoegang:DV:00000001111111111000:entities:9000",
    "metadata_file": os.path.join(
        settings.DJANGO_PROJECT_DIR,
        "authentication",
        "contrib",
        "eherkenning",
        "tests",
        "data",
        "eherkenning-metadata.xml",
    ),
    # SSL/TLS key
    "key_file": os.path.join(
        settings.DJANGO_PROJECT_DIR,
        "authentication",
        "contrib",
        "digid",
        "tests",
        "data",
        "test.key",
    ),
    "cert_file": os.path.join(
        settings.DJANGO_PROJECT_DIR,
        "authentication",
        "contrib",
        "digid",
        "tests",
        "data",
        "test.certificate",
    ),
    "attribute_consuming_service_index": "1",
    "service_loa": "urn:etoegang:core:assurance-class:loa3",
    "oin": "00000001111111111000",
    "service_uuid": "75b40657-ec50-4ced-8e7a-e77d55b46040",
    "service_name": {
        "nl": "Test",
        "en": "Test",
    },
    "service_description": {
        "nl": "Test",
        "en": "Test",
    },
    "service_instance_uuid": "ebd00992-3c8f-4c1c-b28f-d98074de1554",
    "service_url": "https://test-sp.nl",
    "organisation_name": {
        "nl": "Test Organisation",
        "en": "Test Organisation",
    },
    "entity_concerned_types_allowed": [
        {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:RSIN"},
        {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
        {"set_number": "2", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
    ],
    "requested_attributes": [
        "urn:etoegang:1.11:attribute-represented:KvKnr",
    ],
    "privacy_policy_url": {
        "nl": "https://test-sp.nl/privacy_policy",
    },
    "herkenningsmakelaars_id": "00000002222222222000",
}


@override_settings(EHERKENNING=EHERKENNING, CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class AuthenticationStep2Tests(TestCase):
    def test_redirect_to_eherkenning_login(self):
        form = FormFactory.create(authentication_backends=["eherkenning"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "authentication:start",
            kwargs={"slug": form.slug, "plugin_id": "eherkenning"},
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"http://testserver{form_path}"

        response = self.client.get(f"{login_url}?next={form_url}")

        return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": "eherkenning"},
        )
        return_url_with_param = f"{return_url}?next={form_url}"

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)
        self.assertEqual(
            f"http://testserver/eherkenning/login/?{urlencode({'next': return_url_with_param})}",
            response.url,
        )

    @freeze_time("2020-04-09T08:31:46Z")
    @patch(
        "onelogin.saml2.authn_request.OneLogin_Saml2_Utils.generate_unique_id",
        return_value="ONELOGIN_123456",
    )
    def test_authn_request(self, mock_id):
        form = FormFactory.create(authentication_backends=["eherkenning"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "authentication:start",
            kwargs={"slug": form.slug, "plugin_id": "eherkenning"},
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"https://testserver{form_path}"

        response = self.client.get(f"{login_url}?next={form_url}", follow=True)

        return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": "eherkenning"},
        )

        self.assertEqual(
            f"{return_url}?next={form_url}",
            response.context["form"].initial["RelayState"],
        )

        saml_request = b64decode(
            response.context["form"].initial["SAMLRequest"].encode("utf-8")
        )
        tree = etree.fromstring(saml_request)

        self.assertEqual(
            tree.attrib,
            {
                "ID": "ONELOGIN_123456",
                "Version": "2.0",
                "ForceAuthn": "true",
                "IssueInstant": "2020-04-09T08:31:46Z",
                "Destination": "https://test-iwelcome.nl/broker/sso/1.13",
                "ProtocolBinding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Artifact",
                "AssertionConsumerServiceURL": "https://test-sp.nl/eherkenning/acs/",
                "AttributeConsumingServiceIndex": "1",
            },
        )


@override_settings(EHERKENNING=EHERKENNING, CORS_ALLOW_ALL_ORIGINS=True)
@Mocker()
class AuthenticationStep5Tests(TestCase):
    def _create_test_artifact(self, service_entity_id) -> bytes:
        type_code = b"\x00\x04"
        endpoint_index = b"\x00\x00"
        sha_entity_id = sha1(service_entity_id.encode("utf-8")).digest()
        message_handle = b"01234567890123456789"  # something random
        return b64encode(type_code + endpoint_index + sha_entity_id + message_handle)

    @patch(
        "onelogin.saml2.xml_utils.OneLogin_Saml2_XML.validate_xml", return_value=True
    )
    @patch(
        "onelogin.saml2.utils.OneLogin_Saml2_Utils.generate_unique_id",
        return_value="_1330416516",
    )
    @patch(
        "onelogin.saml2.response.OneLogin_Saml2_Response.is_valid", return_value=True
    )
    @patch(
        "digid_eherkenning.saml2.base.BaseSaml2Client.verify_saml2_response",
        return_value=True,
    )
    def test_receive_samlart_from_eHerkenning(
        self,
        m,
        mock_verification,
        mock_validation,
        mock_id,
        mock_xml_validation,
    ):
        with open(
            os.path.join(
                settings.DJANGO_PROJECT_DIR,
                "authentication",
                "contrib",
                "eherkenning",
                "tests",
                "data",
                "ArtifactResponse.xml",
            ),
            "r",
        ) as f:
            artifact_response_success_template = f.read()

        encrypted_attribute = OneLogin_Saml2_Utils.generate_name_id(
            "123456782",
            sp_nq=None,
            nq="urn:etoegang:1.9:EntityConcernedID:KvKnr",
            sp_format="urn:oasis:names:tc:SAML:2.0:nameid-format:persistent",
            cert=open(settings.EHERKENNING["cert_file"], "r").read(),
        )

        artifact_response_soap = (
            Template(artifact_response_success_template)
            .render(Context({"encrypted_attribute": mark_safe(encrypted_attribute)}))
            .encode("utf-8")
        )

        m.post(
            "https://test-iwelcome.nl/broker/ars/1.13",
            content=artifact_response_soap,
        )

        form = FormFactory.create(authentication_backends=["eherkenning"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"https://testserver{form_path}"

        return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": "eherkenning"},
        )
        return_url_with_param = f"https://testserver{return_url}?next={form_url}"

        url = furl(reverse("eherkenning:acs")).set(
            {
                "SAMLart": self._create_test_artifact(
                    EHERKENNING["service_entity_id"]
                ).decode("ascii"),
                "RelayState": return_url_with_param,
            }
        )

        response = self.client.get(url, follow=True)

        self.assertRedirects(
            response,
            form_url,
            status_code=302,
        )

    @patch(
        "onelogin.saml2.xml_utils.OneLogin_Saml2_XML.validate_xml", return_value=True
    )
    @patch(
        "onelogin.saml2.utils.OneLogin_Saml2_Utils.generate_unique_id",
        return_value="_1330416516",
    )
    def test_cancel_login(
        self,
        m,
        mock_id,
        mock_xml_validation,
    ):
        with open(
            os.path.join(
                settings.DJANGO_PROJECT_DIR,
                "authentication",
                "contrib",
                "eherkenning",
                "tests",
                "data",
                "ArtifactResponseCancelLogin.xml",
            ),
            "r",
        ) as f:
            artifact_response_cancel_login_template = f.read()

        artifact_response_soap = (
            Template(artifact_response_cancel_login_template)
            .render(Context({}))
            .encode("utf-8")
        )

        m.post(
            "https://test-iwelcome.nl/broker/ars/1.13",
            content=artifact_response_soap,
        )

        form = FormFactory.create(authentication_backends=["eherkenning"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = furl(f"http://testserver{form_path}")
        form_url.args["_start"] = "1"

        success_return_url = furl(
            reverse(
                "authentication:return",
                kwargs={"slug": form.slug, "plugin_id": "eherkenning"},
            )
        )
        success_return_url.add(args={"next": form_url.url})

        url = furl(reverse("eherkenning:acs")).set(
            {
                "SAMLart": self._create_test_artifact(
                    EHERKENNING["service_entity_id"]
                ).decode("ascii"),
                "RelayState": success_return_url.url,
            }
        )

        response = self.client.get(url, follow=True)

        form_url.args["_eherkenning-message"] = "login-cancelled"

        self.assertEquals(
            response.redirect_chain[-1],
            (form_url.url, 302),
        )
