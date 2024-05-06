from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

import requests_mock
from furl import furl
from rest_framework import status
from rest_framework.test import APIRequestFactory

from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectEHerkenningBewindvoeringConfig,
)
from openforms.authentication.constants import (
    CO_SIGN_PARAMETER,
    FORM_AUTH_SESSION_KEY,
    AuthAttribute,
)
from openforms.authentication.tests.utils import get_start_form_url, get_start_url
from openforms.authentication.views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from openforms.forms.tests.factories import FormFactory

from ...constants import EHERKENNING_BEWINDVOERING_OIDC_AUTH_SESSION_KEY
from ...plugin import EHerkenningBewindvoeringOIDCAuthentication

default_config = OpenIDConnectEHerkenningBewindvoeringConfig(
    enabled=True,
    oidc_rp_client_id="testclient",
    oidc_rp_client_secret="secret",
    oidc_rp_sign_algo="RS256",
    oidc_rp_scopes_list=["openid", "bsn"],
    oidc_op_jwks_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/certs",
    oidc_op_authorization_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/auth",
    oidc_op_token_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/token",
    oidc_op_user_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/userinfo",
)


class MockConfigMixin:
    def setUp(self):
        super().setUp()

        config_patcher = patch(
            "digid_eherkenning_oidc_generics.models"
            ".OpenIDConnectEHerkenningBewindvoeringConfig.get_solo",
            return_value=default_config,
        )
        self.mock_config = config_patcher.start()
        self.addCleanup(config_patcher.stop)


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class EHerkenningBewindvoeringOIDCTests(MockConfigMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.form = FormFactory.create(
            generate_minimal_setup=True,
            authentication_backends=["eherkenning_bewindvoering_oidc"],
        )

    def setUp(self):
        super().setUp()

        self.requests_mocker = requests_mock.Mocker()
        self.addCleanup(self.requests_mocker.stop)
        self.requests_mocker.start()

    def test_redirect_to_eherkenning_bewindvoering_oidc(self):
        self.requests_mocker.get(
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
            status_code=200,
        )
        form_url = get_start_form_url(self.form)
        start_url = get_start_url(self.form, plugin_id="eherkenning_bewindvoering_oidc")

        response = self.client.get(start_url)

        with self.subTest("Sends user to IdP"):
            self.assertEqual(status.HTTP_302_FOUND, response.status_code)

            redirect_target = furl(response.url)  # type: ignore
            query_params = redirect_target.query.params

            self.assertEqual(redirect_target.host, "provider.com")
            self.assertEqual(
                redirect_target.path,
                "/auth/realms/master/protocol/openid-connect/auth",
            )
            self.assertEqual(query_params["scope"], "openid bsn")
            self.assertEqual(query_params["client_id"], "testclient")
            self.assertEqual(
                query_params["redirect_uri"],
                f"http://testserver{reverse('eherkenning_bewindvoering_oidc:oidc_authentication_callback')}",
            )

        with self.subTest("Return state setup"):
            oidc_login_next = furl(self.client.session["oidc_login_next"])
            query_params = oidc_login_next.query.params

            self.assertEqual(
                oidc_login_next.path,
                reverse(
                    "authentication:return",
                    kwargs={
                        "slug": self.form.slug,
                        "plugin_id": "eherkenning_bewindvoering_oidc",
                    },
                ),
            )
            self.assertEqual(query_params["next"], form_url)

    def test_redirect_to_eherkenning_bewindvoering_oidc_internal_server_error(self):
        self.requests_mocker.get(
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
            status_code=500,
        )
        start_url = get_start_url(self.form, plugin_id="eherkenning_bewindvoering_oidc")

        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)
        assert self.requests_mocker.last_request is not None
        self.assertEqual(
            self.requests_mocker.last_request.url,
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
        )
        parsed = furl(response.url)  # type: ignore

        self.assertEqual(parsed.host, "testserver")
        self.assertEqual(parsed.path, f"/{self.form.slug}/")
        query_params = parsed.query.params
        self.assertEqual(
            query_params[BACKEND_OUTAGE_RESPONSE_PARAMETER],
            "eherkenning_bewindvoering_oidc",
        )

    def test_redirect_to_eherkenning_bewindvoering_oidc_callback_error(self):
        # set up session/state
        self.requests_mocker.get(
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
            status_code=200,
        )
        start_url = get_start_url(self.form, plugin_id="eherkenning_bewindvoering_oidc")
        response = self.client.get(start_url)
        assert response.status_code == 302
        assert response.url.startswith("http://provider.com")  # type: ignore

        with patch(
            "openforms.authentication.contrib.digid_eherkenning_oidc.backends"
            ".OIDCAuthenticationEHerkenningBewindvoeringBackend.verify_claims",
            return_value=False,
        ):
            response = self.client.get(
                reverse("eherkenning_bewindvoering_oidc:callback")
            )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.path, f"/{self.form.slug}/")
        self.assertEqual(query_params["_start"], "1")
        self.assertEqual(
            query_params[BACKEND_OUTAGE_RESPONSE_PARAMETER],
            "eherkenning_bewindvoering_oidc",
        )

    @override_settings(CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=[])
    def test_redirect_to_disallowed_domain(self):
        start_url = get_start_url(
            self.form,
            plugin_id="eherkenning_bewindvoering_oidc",
            host="http://example.com",
        )

        response = self.client.get(start_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://example.com"]
    )
    def test_redirect_to_allowed_domain(self):
        self.requests_mocker.get(
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
            status_code=200,
        )
        form_url = get_start_form_url(self.form, host="http://example.com")
        start_url = get_start_url(
            self.form,
            plugin_id="eherkenning_bewindvoering_oidc",
            host="http://example.com",
        )

        response = self.client.get(start_url)

        with self.subTest("Sends user to IdP"):
            self.assertEqual(status.HTTP_302_FOUND, response.status_code)
            self.assertTrue(response.url.startswith("http://provider.com/"))  # type: ignore

        with self.subTest("Return state setup"):
            oidc_login_next = furl(self.client.session["oidc_login_next"])
            expected_next = reverse(
                "authentication:return",
                kwargs={
                    "slug": self.form.slug,
                    "plugin_id": "eherkenning_bewindvoering_oidc",
                },
            )
            self.assertEqual(oidc_login_next.path, expected_next)
            query_params = oidc_login_next.query.params
            self.assertEqual(query_params["next"], form_url)

    def test_redirect_with_keycloak_identity_provider_hint(self):
        self.mock_config.return_value.oidc_keycloak_idp_hint = "oidc-eHerkenning-bewind"
        self.requests_mocker.get(
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
            status_code=200,
        )
        start_url = get_start_url(self.form, plugin_id="eherkenning_bewindvoering_oidc")

        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)
        parsed = furl(response.url)  # type: ignore
        query_params = parsed.query.params
        self.assertEqual(query_params["kc_idp_hint"], "oidc-eHerkenning-bewind")


class AddClaimsToSessionTests(MockConfigMixin, TestCase):
    def test_handle_return_without_claim_eherkenning_bewindvoering(self):
        factory = APIRequestFactory()
        request = factory.get("/xyz")
        request.session = {}  # type: ignore

        plugin = EHerkenningBewindvoeringOIDCAuthentication(identifier="boh")
        plugin.add_claims_to_sessions_if_not_cosigning(claim="", request=request)

        self.assertNotIn(FORM_AUTH_SESSION_KEY, request.session)

    def test_handle_return_with_cosign_param_eherkenning_bewindvoering(self):
        factory = APIRequestFactory()
        request = factory.get(f"/xyz?{CO_SIGN_PARAMETER}=tralala")
        request.session = {}  # type: ignore

        plugin = EHerkenningBewindvoeringOIDCAuthentication(identifier="boh")
        plugin.add_claims_to_sessions_if_not_cosigning(claim="tralala", request=request)

        self.assertNotIn(FORM_AUTH_SESSION_KEY, request.session)

    def test_handle_return_eherkenning_bewindvoering(self):
        factory = APIRequestFactory()
        request = factory.get("/xyz")
        request.session = {  # type: ignore
            EHERKENNING_BEWINDVOERING_OIDC_AUTH_SESSION_KEY: {
                "aanvrager.bsn": "222222222"
            }
        }

        plugin = EHerkenningBewindvoeringOIDCAuthentication(identifier="boh")

        with patch(
            "openforms.authentication.contrib.digid_eherkenning_oidc.plugin.OpenIDConnectEHerkenningBewindvoeringConfig.get_solo",
            return_value=OpenIDConnectEHerkenningBewindvoeringConfig(
                vertegenwoordigde_company_claim_name="gemachtige.kvk",
                gemachtigde_person_claim_name="aanvrager.bsn",
            ),
        ):
            plugin.add_claims_to_sessions_if_not_cosigning(
                claim={
                    "gemachtige.kvk": "111111111",
                },
                request=request,
            )

        self.assertIn(FORM_AUTH_SESSION_KEY, request.session)
        self.assertEqual(
            {
                "plugin": "boh",
                "attribute": AuthAttribute.kvk,
                "value": "111111111",
                "machtigen": {"identifier_value": "222222222"},
            },
            request.session[FORM_AUTH_SESSION_KEY],
        )
