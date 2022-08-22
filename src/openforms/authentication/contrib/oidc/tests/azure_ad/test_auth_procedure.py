from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

import requests_mock
from furl import furl
from mozilla_django_oidc_db.models import OpenIDConnectConfig
from rest_framework import status

from openforms.authentication.views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from openforms.forms.tests.factories import FormFactory

default_config = dict(
    enabled=True,
    oidc_rp_client_id="testclient",
    oidc_rp_client_secret="secret",
    oidc_rp_sign_algo="RS256",
    oidc_rp_scopes_list=["openid", "email", "profile"],
    oidc_op_jwks_endpoint="https://login.microsoftonline.com/test/v2.0/",
    oidc_op_authorization_endpoint="https://login.microsoftonline.com/test/oauth2/v2.0/authorize",
    oidc_op_token_endpoint="https://login.microsoftonline.com/test/oauth2/v2.0/token",
    oidc_op_user_endpoint="https://graph.microsoft.com/oidc/userinfo",
)


@patch(
    "mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo",
    return_value=OpenIDConnectConfig(**default_config),
)
class AzureADOIDCTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.form = FormFactory.create(
            generate_minimal_setup=True, authentication_backends=["azure_ad_oidc"]
        )

    def test_redirect_to_azure_ad_oidc(self, *m):
        login_url = reverse(
            "authentication:start",
            kwargs={"slug": self.form.slug, "plugin_id": "azure_ad_oidc"},
        )

        form_path = reverse("core:form-detail", kwargs={"slug": self.form.slug})
        form_url = str(furl(f"http://testserver{form_path}").set({"_start": "1"}))
        start_url = furl(login_url).set({"next": form_url})
        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.host, "testserver")
        self.assertEqual(parsed.path, reverse("azure_ad_oidc:oidc_authentication_init"))

        parsed = furl(query_params["next"])
        query_params = parsed.query.params

        self.assertEqual(
            parsed.path,
            reverse(
                "authentication:return",
                kwargs={"slug": self.form.slug, "plugin_id": "azure_ad_oidc"},
            ),
        )
        self.assertEqual(query_params["next"], form_url)

        with requests_mock.Mocker() as m:
            m.head(
                "https://login.microsoftonline.com/test/oauth2/v2.0/authorize",
                status_code=200,
            )
            response = self.client.get(response.url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.host, "login.microsoftonline.com")
        self.assertEqual(
            parsed.path,
            "/test/oauth2/v2.0/authorize",
        )
        self.assertEqual(query_params["scope"], "openid email profile")
        self.assertEqual(query_params["client_id"], "testclient")
        self.assertEqual(
            query_params["redirect_uri"],
            f"http://testserver{reverse('azure_ad_oidc:oidc_authentication_callback')}",
        )

        parsed = furl(self.client.session["oidc_login_next"])
        query_params = parsed.query.params

        self.assertEqual(
            parsed.path,
            reverse(
                "authentication:return",
                kwargs={"slug": self.form.slug, "plugin_id": "azure_ad_oidc"},
            ),
        )
        self.assertEqual(query_params["next"], form_url)

    def test_redirect_to_azure_ad_oidc_internal_server_error(self, *m):
        login_url = reverse(
            "authentication:start",
            kwargs={"slug": self.form.slug, "plugin_id": "azure_ad_oidc"},
        )

        form_path = reverse("core:form-detail", kwargs={"slug": self.form.slug})
        form_url = str(furl(f"http://testserver{form_path}").set({"_start": "1"}))
        start_url = furl(login_url).set({"next": form_url})
        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        with requests_mock.Mocker() as m:
            m.head(
                "https://login.microsoftonline.com/test/oauth2/v2.0/authorize",
                status_code=500,
            )
            response = self.client.get(response.url)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.host, "testserver")
        self.assertEqual(parsed.path, form_path)
        self.assertEqual(query_params["of-auth-problem"], "azure_ad_oidc")

    def test_redirect_to_azure_ad_oidc_callback_error(self, *m):
        form_path = reverse("core:form-detail", kwargs={"slug": self.form.slug})
        form_url = f"http://testserver{form_path}"
        redirect_form_url = furl(form_url).set({"_start": "1"})
        redirect_url = furl(
            reverse(
                "authentication:return",
                kwargs={"slug": self.form.slug, "plugin_id": "azure_ad_oidc"},
            )
        ).set({"next": redirect_form_url})

        session = self.client.session
        session["oidc_login_next"] = redirect_url.url
        session.save()

        with patch(
            "openforms.authentication.contrib.oidc.backends.OIDCAuthenticationEHerkenningBackend.verify_claims",
            return_value=False,
        ):
            response = self.client.get(reverse("azure_ad_oidc:callback"))

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.path, form_path)
        self.assertEqual(query_params["_start"], "1")
        self.assertEqual(
            query_params[BACKEND_OUTAGE_RESPONSE_PARAMETER], "azure_ad_oidc"
        )

    @override_settings(CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=[])
    def test_redirect_to_disallowed_domain(self, *m):
        login_url = reverse(
            "azure_ad_oidc:oidc_authentication_init",
        )

        form_url = "http://example.com"
        start_url = str(furl(login_url).set({"next": form_url}))
        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://example.com"]
    )
    def test_redirect_to_allowed_domain(self, *m):
        login_url = reverse(
            "authentication:start",
            kwargs={"slug": self.form.slug, "plugin_id": "azure_ad_oidc"},
        )

        form_url = "http://example.com"
        start_url = str(furl(login_url).set({"next": form_url}))

        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.host, "testserver")
        self.assertEqual(parsed.path, reverse("azure_ad_oidc:oidc_authentication_init"))

        parsed = furl(query_params["next"])
        query_params = parsed.query.params

        self.assertEqual(
            parsed.path,
            reverse(
                "authentication:return",
                kwargs={"slug": self.form.slug, "plugin_id": "azure_ad_oidc"},
            ),
        )
        self.assertEqual(query_params["next"], form_url)

        with requests_mock.Mocker() as m:
            m.head(
                "https://login.microsoftonline.com/test/oauth2/v2.0/authorize",
                status_code=200,
            )
            response = self.client.get(response.url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.host, "login.microsoftonline.com")
        self.assertEqual(parsed.path, "/test/oauth2/v2.0/authorize")
        self.assertEqual(query_params["scope"], "openid email profile")
        self.assertEqual(query_params["client_id"], "testclient")
        self.assertEqual(
            query_params["redirect_uri"],
            f"http://testserver{reverse('azure_ad_oidc:oidc_authentication_callback')}",
        )
