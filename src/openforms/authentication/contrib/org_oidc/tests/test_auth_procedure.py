from unittest.mock import patch

from django.contrib import auth
from django.test import TestCase, override_settings
from django.urls import reverse

import requests_mock
from furl import furl
from mozilla_django_oidc_db.models import OpenIDConnectConfig
from rest_framework import status

from openforms.accounts.models import User
from openforms.authentication.constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.authentication.views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from openforms.forms.tests.factories import FormFactory

default_config = dict(
    enabled=True,
    oidc_rp_client_id="testclient",
    oidc_rp_client_secret="secret",
    oidc_rp_sign_algo="RS256",
    oidc_rp_scopes_list=["openid", "email", "profile"],
    oidc_op_jwks_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/certs",
    oidc_op_authorization_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/auth",
    oidc_op_token_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/token",
    oidc_op_user_endpoint="http://provider.com/auth/realms/master/protocol/openid-connect/userinfo",
    username_claim="sub",
    make_users_staff=True,
)


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class OrgOIDCTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.form = FormFactory.create(
            generate_minimal_setup=True, authentication_backends=["org-oidc"]
        )

    @patch(
        "mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(**default_config),
    )
    def test_redirect_to_org_oidc(self, *m):
        login_url = reverse(
            "authentication:start",
            kwargs={"slug": self.form.slug, "plugin_id": "org-oidc"},
        )

        form_path = reverse("core:form-detail", kwargs={"slug": self.form.slug})
        form_url = str(furl(f"http://testserver{form_path}").set({"_start": "1"}))
        start_url = furl(login_url).set({"next": form_url})
        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.host, "testserver")
        self.assertEqual(parsed.path, reverse("org-oidc:oidc_authentication_init"))

        parsed = furl(query_params["next"])
        query_params = parsed.query.params

        self.assertEqual(
            parsed.path,
            reverse(
                "authentication:return",
                kwargs={"slug": self.form.slug, "plugin_id": "org-oidc"},
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
        self.assertEqual(query_params["scope"], "openid email profile")
        self.assertEqual(query_params["client_id"], "testclient")
        self.assertEqual(
            query_params["redirect_uri"],
            f"http://testserver{reverse('org-oidc:oidc_authentication_callback')}",
        )

        parsed = furl(self.client.session["oidc_login_next"])
        query_params = parsed.query.params

        self.assertEqual(
            parsed.path,
            reverse(
                "authentication:return",
                kwargs={"slug": self.form.slug, "plugin_id": "org-oidc"},
            ),
        )
        self.assertEqual(query_params["next"], form_url)

    @patch(
        "mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(**default_config),
    )
    def test_redirect_to_org_oidc_internal_server_error(self, *m):
        login_url = reverse(
            "authentication:start",
            kwargs={"slug": self.form.slug, "plugin_id": "org-oidc"},
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
        self.assertEqual(query_params["of-auth-problem"], "org-oidc")

    @patch(
        "mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(**default_config),
    )
    def test_redirect_to_org_oidc_callback_error(self, *m):
        form_path = reverse("core:form-detail", kwargs={"slug": self.form.slug})
        form_url = f"http://testserver{form_path}"
        redirect_form_url = furl(form_url).set({"_start": "1"})
        redirect_url = furl(
            reverse(
                "authentication:return",
                kwargs={"slug": self.form.slug, "plugin_id": "org-oidc"},
            )
        ).set({"next": redirect_form_url})

        session = self.client.session
        session["oidc_login_next"] = redirect_url.url
        session.save()

        with patch(
            "openforms.authentication.contrib.org_oidc.backends.OIDCAuthenticationBackend.verify_claims",
            return_value=False,
        ):
            response = self.client.get(reverse("org-oidc:callback"))

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.path, form_path)
        self.assertEqual(query_params["_start"], "1")
        self.assertEqual(query_params[BACKEND_OUTAGE_RESPONSE_PARAMETER], "org-oidc")

    @override_settings(CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=[])
    @patch(
        "mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(**default_config),
    )
    def test_redirect_to_disallowed_domain(self, *m):
        login_url = reverse(
            "org-oidc:oidc_authentication_init",
        )

        form_url = "http://example.com"
        start_url = furl(login_url).set({"next": form_url})
        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://example.com"]
    )
    @patch(
        "mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(**default_config),
    )
    def test_redirect_to_allowed_domain(self, *m):
        login_url = reverse(
            "authentication:start",
            kwargs={"slug": self.form.slug, "plugin_id": "org-oidc"},
        )

        form_url = "http://example.com"
        start_url = furl(login_url).set({"next": form_url})
        response = self.client.get(start_url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = furl(response.url)
        query_params = parsed.query.params

        self.assertEqual(parsed.host, "testserver")
        self.assertEqual(parsed.path, reverse("org-oidc:oidc_authentication_init"))

        parsed = furl(query_params["next"])
        query_params = parsed.query.params

        self.assertEqual(
            parsed.path,
            reverse(
                "authentication:return",
                kwargs={"slug": self.form.slug, "plugin_id": "org-oidc"},
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
        self.assertEqual(query_params["scope"], "openid email profile")
        self.assertEqual(query_params["client_id"], "testclient")
        self.assertEqual(
            query_params["redirect_uri"],
            f"http://testserver{reverse('org-oidc:oidc_authentication_callback')}",
        )

    @patch(
        "openforms.authentication.contrib.org_oidc.backends.OIDCAuthenticationBackend.get_userinfo"
    )
    @patch(
        "openforms.authentication.contrib.org_oidc.backends.OIDCAuthenticationBackend.store_tokens"
    )
    @patch(
        "openforms.authentication.contrib.org_oidc.backends.OIDCAuthenticationBackend.verify_token"
    )
    @patch(
        "openforms.authentication.contrib.org_oidc.backends.OIDCAuthenticationBackend.get_token"
    )
    @patch("mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo")
    def test_callback_url_creates_logged_in_djang_ouser(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        self.assertFalse(User.objects.exists())

        mock_get_solo.return_value = OpenIDConnectConfig(
            **{
                **default_config,
                **{
                    "id": 1,
                    "username_claim": "arbitrary_employee_id_claim",
                    "claim_mapping": {
                        "email": "email",
                        "last_name": "family_name",
                        "first_name": "given_name",
                        "employee_id": "arbitrary_employee_id_claim",
                    },
                },
            }
        )
        mock_get_token.return_value = {
            "id_token": "mock-id-token",
            "access_token": "mock-access-token",
        }
        user_claims = {
            "sub": "arbitrary_employee_id_claim",
            "email": "admin@example.com",
            "given_name": "John",
            "family_name": "Doe",
            "arbitrary_employee_id_claim": "my_id_value",
        }
        mock_verify_token.return_value = user_claims
        mock_get_userinfo.return_value = user_claims
        mock_store_tokens.return_value = {"whatever": 1}

        form_path = reverse("core:form-detail", kwargs={"slug": self.form.slug})
        form_url = f"http://testserver{form_path}"

        f = furl(
            reverse(
                "authentication:return",
                kwargs={"slug": self.form.slug, "plugin_id": "org-oidc"},
            )
        )
        f.args["next"] = form_url
        handle_return_url = f.url

        callback_url = reverse("org-oidc:oidc_authentication_callback")

        session = self.client.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
        session["oidc_login_next"] = handle_return_url
        session.save()

        # check oidc callback view
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response, handle_return_url, fetch_redirect_response=False
        )
        self.assertEqual(status.HTTP_302_FOUND, callback_response.status_code)

        user = User.objects.get()
        self.assertTrue(user.is_staff)
        self.assertTrue(user.username, "some_username")
        self.assertTrue(user.email, "admin@example.com")
        self.assertTrue(user.first_name, "John")
        self.assertTrue(user.last_name, "Doe")
        self.assertTrue(user.employee_id, "my_id_value")

        # check plugins handle_return() response
        return_response = self.client.get(callback_response["Location"])

        self.assertRedirects(return_response, form_url, fetch_redirect_response=False)
        self.assertEqual(status.HTTP_302_FOUND, return_response.status_code)

        self.assertIn(FORM_AUTH_SESSION_KEY, self.client.session)
        s = self.client.session[FORM_AUTH_SESSION_KEY]
        self.assertEqual(s["plugin"], "org-oidc")
        self.assertEqual(s["attribute"], AuthAttribute.employee_id)
        self.assertEqual(s["value"], "my_id_value")

        # django user logged in
        self.assertTrue(auth.get_user(self.client).is_authenticated)
