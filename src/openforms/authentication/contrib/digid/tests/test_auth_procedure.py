import os
from base64 import b64decode, b64encode
from hashlib import sha1
from unittest.mock import patch

from django.conf import settings
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.http import urlencode

from freezegun import freeze_time
from furl import furl
from lxml import etree
from requests_mock import Mocker
from rest_framework import status

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)

DIGID = {
    "base_url": "https://test-sp.nl",
    "entity_id": "https://test-sp.nl",
    "metadata_file": os.path.join(
        settings.DJANGO_PROJECT_DIR,
        "authentication",
        "contrib",
        "digid",
        "tests",
        "data",
        "metadata.xml",
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
    "authn_requests_signed": False,
    "service_entity_id": "https://test-digid.nl",
    "attribute_consuming_service_index": "1",
    "service_name": {
        "nl": "Test",
        "en": "Test",
    },
    "requested_attributes": ["bsn"],
}


@override_settings(DIGID=DIGID, CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class AuthenticationStep2Tests(TestCase):
    def test_redirect_to_digid(self):
        form = FormFactory.create(authentication_backends=["digid"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "authentication:start", kwargs={"slug": form.slug, "plugin_id": "digid"}
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"http://testserver{form_path}?_start=1"

        response = self.client.get(f"{login_url}?next={form_url}")

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        expected_next_path = reverse(
            "authentication:return", kwargs={"slug": form.slug, "plugin_id": "digid"}
        )
        expected_next = furl(expected_next_path).set({"next": form_url}).url
        self.assertEqual(
            furl("http://testserver/digid/login/").set({"next": expected_next}).url,
            response.url,
        )

    @freeze_time("2020-04-09T08:31:46Z")
    @patch(
        "onelogin.saml2.authn_request.OneLogin_Saml2_Utils.generate_unique_id",
        return_value="ONELOGIN_123456",
    )
    def test_authn_request(self, mock_id):
        form = FormFactory.create(authentication_backends=["digid"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "authentication:start", kwargs={"slug": form.slug, "plugin_id": "digid"}
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"https://testserver{form_path}"

        response = self.client.get(f"{login_url}?next={form_url}", follow=True)

        next_parameter = furl(response.context["form"].initial["RelayState"]).args[
            "next"
        ]
        self.assertEqual(form_url, next_parameter)

        saml_request = b64decode(
            response.context["form"].initial["SAMLRequest"].encode("utf-8")
        )
        tree = etree.fromstring(saml_request)

        self.assertEqual(
            tree.attrib,
            {
                "ID": "ONELOGIN_123456",
                "Version": "2.0",
                "IssueInstant": "2020-04-09T08:31:46Z",
                "Destination": "https://test-digid.nl/saml/idp/request_authentication",
                "ProtocolBinding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Artifact",
                "AssertionConsumerServiceURL": "https://test-sp.nl/digid/acs/",
                "AttributeConsumingServiceIndex": "1",
            },
        )


@override_settings(DIGID=DIGID, CORS_ALLOW_ALL_ORIGINS=True)
@Mocker()
class AuthenticationStep5Tests(TestCase):
    def _create_test_artifact(self, service_entity_id):
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
    @patch(
        "onelogin.saml2.response.OneLogin_Saml2_Response.get_nameid",
        return_value="s00000000:12345678",
    )
    def test_receive_samlart_from_digid(
        self,
        m,
        mock_nameid,
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
                "digid",
                "tests",
                "data",
                "ArtifactResponse.xml",
            ),
            "r",
        ) as f:
            artifact_response_success_template = f.read()

        artifact_response_soap = (
            Template(artifact_response_success_template)
            .render(Context({}))
            .encode("utf-8")
        )
        m.post(
            "https://test-digid.nl/saml/idp/resolve_artifact",
            content=artifact_response_soap,
        )

        form = FormFactory.create(authentication_backends=["digid"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"https://testserver{form_path}?_start=1"

        url = (
            reverse("digid:acs")
            + "?"
            + urlencode(
                {
                    "SAMLart": self._create_test_artifact(DIGID["service_entity_id"]),
                    "RelayState": form_url,
                }
            )
        )

        response = self.client.get(url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)
        self.assertEqual(form_url, response.url)

        response = self.client.get(url, follow=True)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("core/views/form/form_detail.html", response.template_name[0])

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
                "digid",
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
            "https://test-digid.nl/saml/idp/resolve_artifact",
            content=artifact_response_soap,
        )

        form = FormFactory.create(authentication_backends=["digid"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"https://testserver{form_path}?_start=1"

        url = (
            reverse("digid:acs")
            + "?"
            + urlencode(
                {
                    "SAMLart": self._create_test_artifact(DIGID["service_entity_id"]),
                    "RelayState": form_url,
                }
            )
        )

        response = self.client.get(url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)
        self.assertEqual(
            form_url + "&_digid-message=login-cancelled", response["location"]
        )
