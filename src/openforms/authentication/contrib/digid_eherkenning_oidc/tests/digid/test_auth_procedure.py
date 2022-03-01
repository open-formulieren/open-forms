from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

import requests_mock
from furl import furl
from rest_framework import status

from digid_eherkenning_oidc_generics.models import OpenIDConnectPublicConfig
from openforms.forms.tests.factories import FormFactory

default_config = dict(
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


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class DigiDOIDCTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.form = FormFactory.create(
            generate_minimal_setup=True, authentication_backends=["digid_oidc"]
        )

    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectPublicConfig.get_solo",
        return_value=OpenIDConnectPublicConfig(**default_config),
    )
    def test_redirect_to_digid_oidc(self, *m):
        login_url = reverse(
            "authentication:start",
            kwargs={"slug": self.form.slug, "plugin_id": "digid_oidc"},
        )

        form_path = reverse("core:form-detail", kwargs={"slug": self.form.slug})
        form_url = str(furl(f"http://testserver{form_path}").set({"_start": "1"}))
        start_url = furl(login_url).set({"next": form_url})
        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.host, "testserver")
        self.assertEqual(parsed.path, reverse("digid_oidc:oidc_authentication_init"))

        parsed = furl(query_params["next"])
        query_params = parsed.query.params

        self.assertEqual(
            parsed.path,
            reverse(
                "authentication:return",
                kwargs={"slug": self.form.slug, "plugin_id": "digid_oidc"},
            ),
        )
        self.assertEqual(query_params["next"], form_url)

        with requests_mock.Mocker() as m:
            m.head(
                "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
                status_code=200,
            )
            response = self.client.get(response.url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.host, "provider.com")
        self.assertEqual(
            parsed.path, "/auth/realms/master/protocol/openid-connect/auth"
        )
        self.assertEqual(query_params["scope"], "openid bsn")
        self.assertEqual(query_params["client_id"], "testclient")
        self.assertEqual(
            query_params["redirect_uri"],
            f"http://testserver{reverse('digid_oidc:oidc_authentication_callback')}",
        )

        parsed = furl(self.client.session["oidc_login_next"])
        query_params = parsed.query.params

        self.assertEqual(
            parsed.path,
            reverse(
                "authentication:return",
                kwargs={"slug": self.form.slug, "plugin_id": "digid_oidc"},
            ),
        )
        self.assertEqual(query_params["next"], form_url)

    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectPublicConfig.get_solo",
        return_value=OpenIDConnectPublicConfig(**default_config),
    )
    def test_redirect_to_digid_oidc_internal_server_error(self, *m):
        login_url = reverse(
            "authentication:start",
            kwargs={"slug": self.form.slug, "plugin_id": "digid_oidc"},
        )

        form_path = reverse("core:form-detail", kwargs={"slug": self.form.slug})
        form_url = str(furl(f"http://testserver{form_path}").set({"_start": "1"}))
        start_url = furl(login_url).set({"next": form_url})
        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        with requests_mock.Mocker() as m:
            m.head(
                "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
                status_code=500,
            )
            response = self.client.get(response.url)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.host, "testserver")
        self.assertEqual(parsed.path, form_path)
        self.assertEqual(query_params["of-auth-problem"], "digid_oidc")

    @override_settings(CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=[])
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectPublicConfig.get_solo",
        return_value=OpenIDConnectPublicConfig(**default_config),
    )
    def test_redirect_to_disallowed_domain(self, *m):
        login_url = reverse(
            "digid_oidc:oidc_authentication_init",
        )

        form_url = "http://example.com"
        start_url = furl(login_url).set({"next": form_url})
        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://example.com"]
    )
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectPublicConfig.get_solo",
        return_value=OpenIDConnectPublicConfig(
            enabled=True,
            oidc_rp_client_id="testclient",
            oidc_rp_client_secret="secret",
            oidc_rp_sign_algo="RS256",
            oidc_rp_scopes_list=["openid", "bsn"],
            oidc_op_jwks_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/certs",
            oidc_op_authorization_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/auth",
            oidc_op_token_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/token",
            oidc_op_user_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/userinfo",
        ),
    )
    def test_redirect_to_allowed_domain(self, *m):
        login_url = reverse(
            "authentication:start",
            kwargs={"slug": self.form.slug, "plugin_id": "digid_oidc"},
        )

        form_url = "http://example.com"
        start_url = furl(login_url).set({"next": form_url})
        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.host, "testserver")
        self.assertEqual(parsed.path, reverse("digid_oidc:oidc_authentication_init"))

        parsed = furl(query_params["next"])
        query_params = parsed.query.params

        self.assertEqual(
            parsed.path,
            reverse(
                "authentication:return",
                kwargs={"slug": self.form.slug, "plugin_id": "digid_oidc"},
            ),
        )
        self.assertEqual(query_params["next"], form_url)

        with requests_mock.Mocker() as m:
            m.head(
                "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
                status_code=200,
            )
            response = self.client.get(response.url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.host, "provider.com")
        self.assertEqual(
            parsed.path, "/auth/realms/master/protocol/openid-connect/auth"
        )
        self.assertEqual(query_params["scope"], "openid bsn")
        self.assertEqual(query_params["client_id"], "testclient")
        self.assertEqual(
            query_params["redirect_uri"],
            f"http://testserver{reverse('digid_oidc:oidc_authentication_callback')}",
        )

    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectPublicConfig.get_solo",
        return_value=OpenIDConnectPublicConfig(
            enabled=True,
            oidc_rp_client_id="testclient",
            oidc_rp_client_secret="secret",
            oidc_rp_sign_algo="RS256",
            oidc_rp_scopes_list=["openid", "bsn"],
            oidc_op_jwks_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/certs",
            oidc_op_authorization_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/auth",
            oidc_op_token_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/token",
            oidc_op_user_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/userinfo",
            oidc_keycloak_idp_hint="oidc-digid",
        ),
    )
    def test_redirect_with_keycloak_identity_provider_hint(self, *m):
        login_url = reverse(
            "authentication:start",
            kwargs={"slug": self.form.slug, "plugin_id": "digid_oidc"},
        )

        form_path = reverse("core:form-detail", kwargs={"slug": self.form.slug})
        form_url = str(furl(f"http://testserver{form_path}").set({"_start": "1"}))
        start_url = furl(login_url).set({"next": form_url})
        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.host, "testserver")
        self.assertEqual(parsed.path, reverse("digid_oidc:oidc_authentication_init"))

        parsed = furl(query_params["next"])
        query_params = parsed.query.params

        self.assertEqual(
            parsed.path,
            reverse(
                "authentication:return",
                kwargs={"slug": self.form.slug, "plugin_id": "digid_oidc"},
            ),
        )
        self.assertEqual(query_params["next"], form_url)

        with requests_mock.Mocker() as m:
            m.head(
                "http://provider.com/auth/realms/master/protocol/openid-connect/auth",
                status_code=200,
            )
            response = self.client.get(response.url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.host, "provider.com")
        self.assertEqual(
            parsed.path, "/auth/realms/master/protocol/openid-connect/auth"
        )
        self.assertEqual(query_params["scope"], "openid bsn")
        self.assertEqual(query_params["client_id"], "testclient")
        self.assertEqual(
            query_params["redirect_uri"],
            f"http://testserver{reverse('digid_oidc:oidc_authentication_callback')}",
        )
        self.assertEqual(query_params["kc_idp_hint"], "oidc-digid")
