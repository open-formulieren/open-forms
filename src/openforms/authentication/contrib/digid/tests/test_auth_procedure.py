import os
from base64 import b64decode, b64encode
from hashlib import sha1
from typing import Optional
from unittest.mock import patch

from django.conf import settings
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import reverse

import requests_mock
from freezegun import freeze_time
from furl import furl
from lxml import etree
from rest_framework import status

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ....constants import CO_SIGN_PARAMETER, FORM_AUTH_SESSION_KEY, AuthAttribute

TEST_FILES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

DIGID = {
    "base_url": "https://test-sp.nl",
    "entity_id": "https://test-sp.nl",
    "metadata_file": os.path.join(TEST_FILES, "metadata.xml"),
    # SSL/TLS key
    "key_file": os.path.join(TEST_FILES, "test.key"),
    "cert_file": os.path.join(TEST_FILES, "test.certificate"),
    "authn_requests_signed": False,
    "service_entity_id": "https://test-digid.nl",
    "attribute_consuming_service_index": "1",
    "service_name": {
        "nl": "Test",
        "en": "Test",
    },
    "requested_attributes": ["bsn"],
}


def _create_test_artifact(service_entity_id: str = "") -> str:
    if not service_entity_id:
        service_entity_id = settings.DIGID["service_entity_id"]
    type_code = b"\x00\x04"
    endpoint_index = b"\x00\x00"
    sha_entity_id = sha1(service_entity_id.encode("utf-8")).digest()
    message_handle = b"01234567890123456789"  # something random
    b64encoded = b64encode(type_code + endpoint_index + sha_entity_id + message_handle)
    return b64encoded.decode("ascii")


def _get_artifact_response(filename: str, context: Optional[dict] = None) -> bytes:
    filepath = os.path.join(TEST_FILES, filename)
    with open(filepath, "r") as template_source_file:
        template = Template(template_source_file.read())

    rendered = template.render(Context(context or {}))
    return rendered.encode("utf-8")


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
            },
        )


@override_settings(DIGID=DIGID, CORS_ALLOW_ALL_ORIGINS=True)
@requests_mock.Mocker()
class AuthenticationStep5Tests(TestCase):
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
        m.post(
            "https://test-digid.nl/saml/idp/resolve_artifact",
            content=_get_artifact_response("ArtifactResponse.xml"),
        )

        form = FormFactory.create(authentication_backends=["digid"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"https://testserver{form_path}?_start=1"
        auth_return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": "digid"},
        )
        relay_state = furl(auth_return_url).set({"next": form_url})

        url = furl(reverse("digid:acs")).set(
            {
                "SAMLart": _create_test_artifact(),
                "RelayState": str(relay_state),
            }
        )

        response = self.client.get(url)

        self.assertRedirects(response, str(relay_state), fetch_redirect_response=False)

        response = self.client.get(url, follow=True)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertTemplateUsed(response, "core/views/form/form_detail.html")
        self.assertEqual(
            self.client.session[FORM_AUTH_SESSION_KEY],
            {"plugin": "digid", "attribute": AuthAttribute.bsn, "value": "12345678"},
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
        m.post(
            "https://test-digid.nl/saml/idp/resolve_artifact",
            content=_get_artifact_response("ArtifactResponseCancelLogin.xml"),
        )

        form = FormFactory.create(authentication_backends=["digid"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = furl(f"http://testserver{form_path}")
        form_url.args["_start"] = "1"

        success_return_url = furl(
            reverse(
                "authentication:return",
                kwargs={"slug": form.slug, "plugin_id": "digid"},
            )
        )
        success_return_url.add(args={"next": form_url.url})

        url = furl(reverse("digid:acs")).set(
            {
                "SAMLart": _create_test_artifact(),
                "RelayState": success_return_url.url,
            }
        )

        response = self.client.get(url, follow=True)

        form_url.args["_digid-message"] = "login-cancelled"

        self.assertEquals(
            response.redirect_chain[-1],
            (form_url.url, 302),
        )


@override_settings(DIGID=DIGID, CORS_ALLOW_ALL_ORIGINS=True)
@requests_mock.Mocker()
class CoSignLoginAuthenticationTests(SubmissionsMixin, TestCase):
    @freeze_time("2020-04-09T08:31:46Z")
    @patch(
        "onelogin.saml2.authn_request.OneLogin_Saml2_Utils.generate_unique_id",
        return_value="ONELOGIN_123456",
    )
    def test_authn_request_for_co_sign(self, m, mock_id):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            form__slug="myform",
            form__authentication_backends=["digid"],
        )
        self._add_submission_to_session(submission)
        form_url = "http://localhost:3000"
        login_url = reverse(
            "authentication:start", kwargs={"slug": "myform", "plugin_id": "digid"}
        )

        start_response = self.client.get(
            login_url,
            {"next": form_url, CO_SIGN_PARAMETER: submission.uuid},
            follow=True,
        )

        # form that auto-submits to DigiD
        self.assertEqual(start_response.status_code, 200)
        relay_state = furl(start_response.context["form"].initial["RelayState"])
        self.assertIn(CO_SIGN_PARAMETER, relay_state.args)
        self.assertEqual(relay_state.args[CO_SIGN_PARAMETER], str(submission.uuid))

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
    def test_return_with_samlart_from_digid(
        self,
        m,
        mock_nameid,
        mock_verification,
        mock_validation,
        mock_id,
        mock_xml_validation,
    ):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            form__slug="myform",
            form__authentication_backends=["digid"],
        )
        self._add_submission_to_session(submission)
        auth_return_url = reverse(
            "authentication:return",
            kwargs={"slug": "myform", "plugin_id": "digid"},
        )
        auth_return_url = furl(auth_return_url).set({"next": "http://localhost:3000"})
        m.post(
            "https://test-digid.nl/saml/idp/resolve_artifact",
            content=_get_artifact_response("ArtifactResponse.xml"),
        )
        # set the relay-state, see test ``test_authn_request_for_co_sign`` for the
        # expected querystring args
        relay_state = auth_return_url.add(
            {
                CO_SIGN_PARAMETER: str(submission.uuid),
            }
        )
        url = furl(reverse("digid:acs")).set(
            {
                "SAMLart": _create_test_artifact(),
                "RelayState": relay_state,
            }
        )

        response = self.client.get(url)
        self.assertRedirects(
            response, str(auth_return_url), fetch_redirect_response=False
        )
        response = self.client.get(response["Location"])

        self.assertRedirects(
            response, "http://localhost:3000", fetch_redirect_response=False
        )
        # we don't expect the auth parameters to be set, as this is a co-sign request
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.client.session)
        submission.refresh_from_db()
        self.assertEqual(
            submission.co_sign_data,
            {"plugin": "digid", "identifier": "12345678", "fields": {}},
        )
