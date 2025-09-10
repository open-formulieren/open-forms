from base64 import b64decode
from datetime import datetime, timedelta
from unittest.mock import patch

from django.core.files import File
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

import requests_mock
from digid_eherkenning.choices import ConfigTypes, DigiDAssuranceLevels
from digid_eherkenning.models import ConfigCertificate, DigidConfiguration
from furl import furl
from lxml import etree
from privates.test import temp_private_root
from rest_framework import status
from simple_certmanager.test.factories import CertificateFactory

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin
from openforms.utils.tests.cache import clear_caches

from ....constants import CO_SIGN_PARAMETER, FORM_AUTH_SESSION_KEY, AuthAttribute
from ....contrib.tests.saml_utils import create_test_artifact, get_artifact_response
from ..constants import DIGID_DEFAULT_LOA
from .utils import TEST_FILES


def _create_test_artifact() -> str:
    config = DigidConfiguration.get_solo()
    return create_test_artifact(config.idp_service_entity_id)


def _get_artifact_response(filename: str, context: dict | None = None) -> bytes:
    path = str(TEST_FILES / filename)
    return get_artifact_response(path, context=context)


class DigiDConfigMixin:
    """
    Configure DigiD for testing purposes.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cert = CertificateFactory.create(label="DigiD", with_private_key=True)

        METADATA = TEST_FILES / "metadata.xml"

        config = DigidConfiguration.get_solo()
        config.base_url = "https://test-sp.nl"
        config.entity_id = "https://test-sp.nl"
        # config.authn_requests_signed =  False
        config.idp_service_entity_id = "https://test-digid.nl"
        config.attribute_consuming_service_index = "1"
        config.service_name = "Test"
        config.requested_attributes = ["bsn"]
        config.want_assertions_signed = False
        config.slo = False

        with METADATA.open("rb") as md_file:
            config.idp_metadata_file = File(md_file, METADATA.name)
            config.save()

        config_cert = ConfigCertificate.objects.create(
            config_type=ConfigTypes.digid, certificate=cert
        )
        # Will fail if/when the certificate expires
        assert config_cert.is_ready_for_authn_requests

    def setUp(self):
        super().setUp()

        clear_caches()
        self.addCleanup(clear_caches)


@temp_private_root()
@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class AuthenticationStep2Tests(DigiDConfigMixin, TestCase):
    def test_redirect_to_digid(self):
        form = FormFactory.create(
            authentication_backend="digid",
            authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
        )
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

    def test_authn_request_without_digid_authentication_backend(self):
        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "authentication:start", kwargs={"slug": form.slug, "plugin_id": "digid"}
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"https://testserver{form_path}"

        response = self.client.get(f"{login_url}?next={form_url}", follow=True)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(b"plugin not allowed", response.content)

    def test_direct_digid_login_request_without_digid_authentication_backend(self):
        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse("digid:login")
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"https://testserver{form_path}"

        response = self.client.get(f"{login_url}?next={form_url}", follow=True)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    @patch(
        "onelogin.saml2.authn_request.OneLogin_Saml2_Utils.generate_unique_id",
        return_value="ONELOGIN_123456",
    )
    def test_authn_request(self, mock_id):
        form = FormFactory.create(
            authentication_backend="digid",
            authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
        )
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "authentication:start", kwargs={"slug": form.slug, "plugin_id": "digid"}
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"https://testserver{form_path}"
        now = timezone.now()

        response = self.client.get(f"{login_url}?next={form_url}", follow=True)

        next_parameter = furl(response.context["form"].initial["RelayState"]).args[
            "next"
        ]
        self.assertEqual(form_url, next_parameter)

        saml_request = b64decode(
            response.context["form"].initial["SAMLRequest"].encode("utf-8")
        )
        tree = etree.fromstring(saml_request)

        expected_attributes = {
            "ID": "ONELOGIN_123456",
            "Version": "2.0",
            "Destination": "https://test-digid.nl/saml/idp/request_authentication",
            "ProtocolBinding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Artifact",
            "AssertionConsumerServiceURL": "https://test-sp.nl/digid/acs/",
        }
        for key, expected_value in expected_attributes.items():
            with self.subTest(attribute=key):
                value = tree.attrib[key]

                self.assertEqual(value, expected_value)

        with self.subTest(attribute="IssueInstant"):
            try:
                issue_instant = datetime.fromisoformat(tree.attrib["IssueInstant"])
            except Exception as exc:
                raise self.failureException("Not a valid timestamp") from exc
            self.assertTrue(
                now.replace(microsecond=0)
                <= issue_instant
                < (now + timedelta(seconds=3))
            )

    @patch(
        "onelogin.saml2.authn_request.OneLogin_Saml2_Utils.generate_unique_id",
        return_value="ONELOGIN_123456",
    )
    def test_authn_request_uses_minimal_loa_from_form(self, mock_id):
        form = FormFactory.create(
            authentication_backend="digid",
            authentication_backend_options={"loa": DigiDAssuranceLevels.substantial},
        )
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

        auth_context_class_ref = tree.xpath(
            "samlp:RequestedAuthnContext[@Comparison='minimum']/saml:AuthnContextClassRef",
            namespaces={
                "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
                "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
            },
        )[0]

        self.assertEqual(
            auth_context_class_ref.text, DigiDAssuranceLevels.substantial.value
        )

    @patch(
        "onelogin.saml2.authn_request.OneLogin_Saml2_Utils.generate_unique_id",
        return_value="ONELOGIN_123456",
    )
    def test_authn_request_uses_default_loa_if_not_overriden(self, mock_id):
        form = FormFactory.create(
            authentication_backend="digid",
            authentication_backend_options={},
        )
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

        auth_context_class_ref = tree.xpath(
            "samlp:RequestedAuthnContext[@Comparison='minimum']/saml:AuthnContextClassRef",
            namespaces={
                "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
                "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
            },
        )[0]

        self.assertEqual(auth_context_class_ref.text, DigiDAssuranceLevels.middle.value)


@temp_private_root()
@override_settings(CORS_ALLOW_ALL_ORIGINS=True)
@requests_mock.Mocker()
class AuthenticationStep5Tests(DigiDConfigMixin, TestCase):
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

        form = FormFactory.create(
            authentication_backend="digid",
            authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
        )
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
        self.assertTemplateUsed(response, "forms/form_detail.html")
        self.assertEqual(
            self.client.session[FORM_AUTH_SESSION_KEY],
            {
                "plugin": "digid",
                "attribute": AuthAttribute.bsn,
                "value": "12345678",
                "loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
            },
        )

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
        return_value="12345678",
    )
    def test_receive_samlart_without_sector_code_from_digid(
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

        form = FormFactory.create(
            authentication_backend="digid",
            authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
        )
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
        self.assertTemplateUsed(response, "forms/form_detail.html")
        self.assertEqual(
            self.client.session[FORM_AUTH_SESSION_KEY],
            {
                "plugin": "digid",
                "attribute": AuthAttribute.bsn,
                "value": "12345678",
                "loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
            },
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

        form = FormFactory.create(
            authentication_backend="digid",
            authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
        )
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

        self.assertEqual(
            response.redirect_chain[-1],
            (form_url.url, 302),
        )


@temp_private_root()
@override_settings(CORS_ALLOW_ALL_ORIGINS=True)
@requests_mock.Mocker()
class CoSignLoginAuthenticationTests(SubmissionsMixin, DigiDConfigMixin, TestCase):
    @patch(
        "onelogin.saml2.authn_request.OneLogin_Saml2_Utils.generate_unique_id",
        return_value="ONELOGIN_123456",
    )
    def test_authn_request_for_co_sign(self, m, mock_id):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            form__slug="myform",
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
        )
        self._add_submission_to_session(submission)
        form_path = reverse("core:form-detail", kwargs={"slug": submission.form.slug})
        form_url = furl("http://localhost:3000") / form_path
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
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
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
            {
                "version": "v1",
                "plugin": "digid",
                "identifier": "12345678",
                "representation": "",
                "co_sign_auth_attribute": "bsn",
                "fields": {},
            },
        )
