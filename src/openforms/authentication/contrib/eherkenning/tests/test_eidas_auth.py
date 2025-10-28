import os
import sys
from base64 import b64decode
from datetime import datetime, timedelta
from unittest.mock import patch

from django.core.files import File
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

import requests_mock
from digid_eherkenning.choices import ConfigTypes
from digid_eherkenning.models import ConfigCertificate, EherkenningConfiguration
from furl import furl
from lxml import etree
from privates.test import temp_private_root
from simple_certmanager.test.factories import CertificateFactory

from openforms.forms.tests.factories import FormFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin
from openforms.tests.utils import supress_output
from openforms.utils.tests.cache import clear_caches

from ....constants import CO_SIGN_PARAMETER, FORM_AUTH_SESSION_KEY, AuthAttribute
from ....contrib.tests.saml_utils import (
    create_test_artifact,
    get_artifact_response,
    get_encrypted_attribute,
)
from .utils import TEST_FILES, mock_saml2_return_flow


class EIDASConfigMixin:
    """
    Configure DigiD for testing purposes.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()  # pyright: ignore[reportAttributeAccessIssue]

        cert = CertificateFactory.create(label="eHerkenning", with_private_key=True)

        METADATA = TEST_FILES / "eherkenning-metadata.xml"

        config = EherkenningConfiguration.get_solo()
        config.base_url = "https://test-sp.nl"
        config.entity_id = "urn:etoegang:DV:00000001111111111000:entities:9000"
        config.idp_service_entity_id = (
            "urn:etoegang:DV:00000001111111111000:entities:9000"
        )
        config.service_name = "Test eIDAS"
        config.service_description = "Test eIDAS"
        config.want_assertions_signed = False
        config.eh_loa = "urn:etoegang:core:assurance-class:loa3"
        config.privacy_policy = "https://test-sp.nl/privacy_policy"
        config.makelaar_id = "00000002222222222000"
        config.oin = "00000001111111111000"
        config.organization_name = "Test Organisation"
        config.no_eidas = False

        config.eidas_attribute_consuming_service_index = "9999"
        config.eidas_requested_attributes = []
        config.eidas_loa = "urn:etoegang:core:assurance-class:loa3"
        config.eidas_service_uuid = "75b40657-ec50-4ced-8e7a-e77d55b46040"
        config.eidas_service_instance_uuid = "ebd00992-3c8f-4c1c-b28f-d98074de1554"

        with METADATA.open("rb") as md_file:
            config.idp_metadata_file = File(md_file, METADATA.name)
            config.save()

        config_cert = ConfigCertificate.objects.create(
            config_type=ConfigTypes.eherkenning, certificate=cert
        )
        # Will fail if/when the certificate expires
        assert config_cert.is_ready_for_authn_requests

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()  # pyright: ignore[reportAttributeAccessIssue]

    def setUp(self):
        super().setUp()  # pyright: ignore[reportAttributeAccessIssue]

        clear_caches()
        self.addCleanup(clear_caches)  # pyright: ignore[reportAttributeAccessIssue]


def _create_test_artifact() -> str:
    config = EherkenningConfiguration.get_solo()
    return create_test_artifact(config.idp_service_entity_id)


def _get_artifact_response(filename: str, context: dict | None = None) -> bytes:
    filepath = TEST_FILES / filename
    return get_artifact_response(str(filepath), context=context)


def _get_encrypted_attribute(pseudo_id: str):
    return get_encrypted_attribute("Pseudo", pseudo_id)


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
@temp_private_root()
class AuthenticationStep2Tests(EIDASConfigMixin, TestCase):
    def test_redirect_to_eIDAS_login(self):
        form = FormFactory.create(
            authentication_backend="eidas",
            generate_minimal_setup=True,
            formstep__form_definition__login_required=True,
        )
        login_url = reverse(
            "authentication:start",
            kwargs={"slug": form.slug, "plugin_id": "eidas"},
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"http://testserver{form_path}"

        response = self.client.get(login_url, {"next": form_url})

        return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": "eidas"},
        )
        return_url_with_param = furl(return_url).set({"next": form_url})

        # We always get redirected to the /eherkenning/login/ url, but the attr_consuming_service_index differentiates
        # between the eHerkenning and the eIDAS flow
        expected_redirect_url = furl("http://testserver/eherkenning/login/").set(
            {
                "next": return_url_with_param,
                "attr_consuming_service_index": "9999",
            }
        )
        self.assertRedirects(
            response, str(expected_redirect_url), fetch_redirect_response=False
        )

    @patch(
        "onelogin.saml2.authn_request.OneLogin_Saml2_Utils.generate_unique_id",
        return_value="ONELOGIN_123456",
    )
    def test_authn_request(self, mock_id):
        form = FormFactory.create(
            authentication_backend="eidas",
            generate_minimal_setup=True,
            formstep__form_definition__login_required=True,
        )
        login_url = reverse(
            "authentication:start",
            kwargs={"slug": form.slug, "plugin_id": "eidas"},
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"https://testserver{form_path}"
        login_url = furl(login_url).set({"next": form_url})
        now = timezone.now()

        response = self.client.get(login_url.url, follow=True)

        return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": "eidas"},
        )

        self.assertEqual(
            response.context["form"].initial["RelayState"],
            str(furl(return_url).set({"next": form_url})),
        )

        saml_request = b64decode(
            response.context["form"].initial["SAMLRequest"].encode("utf-8")
        )
        tree = etree.fromstring(saml_request)

        expected_attributes = {
            "ID": "ONELOGIN_123456",
            "Version": "2.0",
            "ForceAuthn": "true",
            "Destination": "https://test-iwelcome.nl/broker/sso/1.13",
            "ProtocolBinding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Artifact",
            "AssertionConsumerServiceURL": "https://test-sp.nl/eherkenning/acs/",
            "AttributeConsumingServiceIndex": "9999",
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


@override_settings(CORS_ALLOW_ALL_ORIGINS=True)
@temp_private_root()
@requests_mock.Mocker()
class AuthenticationStep5Tests(EIDASConfigMixin, TestCase):
    @mock_saml2_return_flow(mock_saml_art_verification=True)
    def test_receive_samlart_from_eHerkenning(self, m):
        encrypted_attribute = _get_encrypted_attribute("123456782")
        m.post(
            "https://test-iwelcome.nl/broker/ars/1.13",
            content=_get_artifact_response(
                "EIDASArtifactResponse.xml",
                {"encrypted_attribute": mark_safe(encrypted_attribute)},
            ),
        )
        form = FormFactory.create(
            authentication_backend="eidas",
            generate_minimal_setup=True,
            formstep__form_definition__login_required=True,
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": "eidas"},
        )
        return_url_with_param = furl(f"https://testserver{return_url}").set(
            {"next": f"https://testserver{form_path}"}
        )

        url = furl(reverse("eherkenning:acs")).set(
            {
                "SAMLart": _create_test_artifact(),
                "RelayState": str(return_url_with_param),
            }
        )

        with supress_output(sys.stderr, os.devnull):
            response = self.client.get(url, follow=True)

        self.assertRedirects(
            response, f"https://testserver{form_path}", status_code=302
        )

        self.assertIn(FORM_AUTH_SESSION_KEY, self.client.session)
        session_data = self.client.session[FORM_AUTH_SESSION_KEY]
        self.assertEqual(session_data["attribute"], AuthAttribute.pseudo)
        self.assertEqual(session_data["value"], "123456782")

    @mock_saml2_return_flow(mock_saml_art_verification=False)
    def test_cancel_login(self, m):
        m.post(
            "https://test-iwelcome.nl/broker/ars/1.13",
            content=_get_artifact_response("ArtifactResponseCancelLogin.xml"),
        )
        form = FormFactory.create(
            authentication_backend="eidas",
            generate_minimal_setup=True,
            formstep__form_definition__login_required=True,
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = furl(f"http://testserver{form_path}")
        form_url.args["_start"] = "1"

        success_return_url = furl(
            reverse(
                "authentication:return",
                kwargs={"slug": form.slug, "plugin_id": "eidas"},
            )
        )
        success_return_url.add(args={"next": form_url.url})

        # The ACS is the same as for eHerkenning!
        url = furl(reverse("eherkenning:acs")).set(
            {
                "SAMLart": _create_test_artifact(),
                "RelayState": success_return_url.url,
            }
        )

        response = self.client.get(url, follow=True)

        form_url.args["_eidas-message"] = "login-cancelled"

        self.assertEqual(
            response.redirect_chain[-1],
            (form_url.url, 302),
        )


@override_settings(CORS_ALLOW_ALL_ORIGINS=True)
@temp_private_root()
@requests_mock.Mocker()
class CoSignLoginAuthenticationTests(SubmissionsMixin, EIDASConfigMixin, TestCase):
    @patch(
        "onelogin.saml2.authn_request.OneLogin_Saml2_Utils.generate_unique_id",
        return_value="ONELOGIN_123456",
    )
    def test_authn_request_for_co_sign(self, m, mock_id):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            form__slug="myform",
            form__authentication_backend="eidas",
        )
        self._add_submission_to_session(submission)
        form_url = "http://localhost:3000"
        login_url = reverse(
            "authentication:start",
            kwargs={"slug": "myform", "plugin_id": "eidas"},
        )

        start_response = self.client.get(
            login_url,
            {"next": form_url, CO_SIGN_PARAMETER: submission.uuid},
            follow=True,
        )

        # form that auto-submits to eIDAS
        self.assertEqual(start_response.status_code, 200)
        relay_state = furl(start_response.context["form"].initial["RelayState"])
        self.assertIn(CO_SIGN_PARAMETER, relay_state.args)
        self.assertEqual(relay_state.args[CO_SIGN_PARAMETER], str(submission.uuid))

    @mock_saml2_return_flow(mock_saml_art_verification=True)
    def test_return_with_samlart_from_eidas(self, m):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            form__slug="myform",
            form__authentication_backend="eidas",
        )
        self._add_submission_to_session(submission)
        auth_return_url = reverse(
            "authentication:return",
            kwargs={"slug": "myform", "plugin_id": "eidas"},
        )
        auth_return_url = furl(auth_return_url).set({"next": "http://localhost:3000"})
        encrypted_attribute = _get_encrypted_attribute("112233445")
        m.post(
            "https://test-iwelcome.nl/broker/ars/1.13",
            content=_get_artifact_response(
                "ArtifactResponse.xml",
                {"encrypted_attribute": mark_safe(encrypted_attribute)},
            ),
        )
        # set the relay-state, see test ``test_authn_request_for_co_sign`` for the
        # expected querystring args
        relay_state = auth_return_url.add(
            {
                CO_SIGN_PARAMETER: str(submission.uuid),
            }
        )
        url = furl(reverse("eherkenning:acs")).set(
            {
                "SAMLart": _create_test_artifact(),
                "RelayState": relay_state,
            }
        )

        with supress_output(sys.stderr, os.devnull):
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
                "plugin": "eidas",
                "identifier": "112233445",
                "representation": "",
                "co_sign_auth_attribute": "pseudo",
                "fields": {},
            },
        )
