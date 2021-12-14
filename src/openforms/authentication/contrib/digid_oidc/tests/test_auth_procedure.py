from urllib.parse import parse_qs, urlparse

from django.test import TestCase, override_settings
from django.urls import reverse

import requests_mock
from rest_framework import status

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)

from ..models import OpenIDConnectPublicConfig


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class DigiDOIDCTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = OpenIDConnectPublicConfig.get_solo()
        config.enabled = True
        config.oidc_rp_client_id = "testclient"
        config.oidc_rp_client_secret = "secret"
        config.oidc_rp_sign_algo = "RS256"
        config.oidc_rp_scopes_list = ["openid", "bsn"]
        config.oidc_redirect_allowed_hosts = []

        config.oidc_op_jwks_endpoint = (
            "http://identityprovider/auth/realms/master/protocol/openid-connect/certs"
        )
        config.oidc_op_authorization_endpoint = (
            "http://identityprovider/auth/realms/master/protocol/openid-connect/auth"
        )
        config.oidc_op_token_endpoint = (
            "http://identityprovider/auth/realms/master/protocol/openid-connect/token"
        )
        config.oidc_op_user_endpoint = "http://identityprovider/auth/realms/master/protocol/openid-connect/userinfo"
        config.save()

    def test_redirect_to_digid_oidc(self):
        form = FormFactory.create(authentication_backends=["digid_oidc"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "authentication:start",
            kwargs={"slug": form.slug, "plugin_id": "digid_oidc"},
        )

        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"http://testserver{form_path}?_start=1"

        response = self.client.get(f"{login_url}?next={form_url}")

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = urlparse(response.url)
        query_params = parse_qs(parsed.query)
        self.assertEqual(parsed.hostname, "testserver")
        self.assertEqual(parsed.path, reverse("digid_oidc:oidc_authentication_init"))

        parsed = urlparse(query_params["next"][0])
        query_params = parse_qs(parsed.query)
        self.assertEqual(
            parsed.path,
            reverse(
                "authentication:return",
                kwargs={"slug": form.slug, "plugin_id": "digid_oidc"},
            ),
        )
        self.assertEqual(query_params["next"][0], form_url)

        with requests_mock.Mocker() as m:
            m.head(
                "http://identityprovider/auth/realms/master/protocol/openid-connect/auth",
                status_code=200,
            )
            response = self.client.get(response.url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = urlparse(response.url)
        query_params = parse_qs(parsed.query)
        self.assertEqual(parsed.hostname, "identityprovider")
        self.assertEqual(
            parsed.path, "/auth/realms/master/protocol/openid-connect/auth"
        )
        self.assertEqual(query_params["scope"][0], "openid bsn")
        self.assertEqual(query_params["client_id"][0], "testclient")
        self.assertEqual(
            query_params["redirect_uri"][0],
            f"http://testserver{reverse('digid_oidc:oidc_authentication_callback')}",
        )

        parsed = urlparse(self.client.session["oidc_login_next"])
        query_params = parse_qs(parsed.query)
        self.assertEqual(
            parsed.path,
            reverse(
                "authentication:return",
                kwargs={"slug": form.slug, "plugin_id": "digid_oidc"},
            ),
        )
        self.assertEqual(query_params["next"][0], form_url)

    def test_redirect_to_digid_oidc_internal_server_error(self):
        form = FormFactory.create(authentication_backends=["digid_oidc"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "authentication:start",
            kwargs={"slug": form.slug, "plugin_id": "digid_oidc"},
        )

        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"http://testserver{form_path}?_start=1"

        response = self.client.get(f"{login_url}?next={form_url}")

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        with requests_mock.Mocker() as m:
            m.head(
                "http://identityprovider/auth/realms/master/protocol/openid-connect/auth",
                status_code=500,
            )
            response = self.client.get(response.url)

        parsed = urlparse(response.url)
        query_params = parse_qs(parsed.query)

        self.assertEqual(parsed.hostname, "testserver")
        self.assertEqual(parsed.path, form_path)
        self.assertEqual(query_params["of-auth-problem"][0], "digid_oidc")

    def test_redirect_to_disallowed_domain(self):
        config = OpenIDConnectPublicConfig().get_solo()
        config.oidc_redirect_allowed_hosts = []
        config.save()

        form = FormFactory.create(authentication_backends=["digid_oidc"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "digid_oidc:oidc_authentication_init",
        )

        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = "http://example.com"

        response = self.client.get(f"{login_url}?next={form_url}")

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_redirect_to_allowed_domain(self):
        config = OpenIDConnectPublicConfig.get_solo()
        config.oidc_redirect_allowed_hosts = ["example.com"]
        config.save()

        form = FormFactory.create(authentication_backends=["digid_oidc"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "authentication:start",
            kwargs={"slug": form.slug, "plugin_id": "digid_oidc"},
        )

        form_url = "http://example.com"

        response = self.client.get(f"{login_url}?next={form_url}")

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = urlparse(response.url)
        query_params = parse_qs(parsed.query)
        self.assertEqual(parsed.hostname, "testserver")
        self.assertEqual(parsed.path, reverse("digid_oidc:oidc_authentication_init"))

        parsed = urlparse(query_params["next"][0])
        query_params = parse_qs(parsed.query)
        self.assertEqual(
            parsed.path,
            reverse(
                "authentication:return",
                kwargs={"slug": form.slug, "plugin_id": "digid_oidc"},
            ),
        )
        self.assertEqual(query_params["next"][0], form_url)

        with requests_mock.Mocker() as m:
            m.head(
                "http://identityprovider/auth/realms/master/protocol/openid-connect/auth",
                status_code=200,
            )
            response = self.client.get(response.url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = urlparse(response.url)
        query_params = parse_qs(parsed.query)
        self.assertEqual(parsed.hostname, "identityprovider")
        self.assertEqual(
            parsed.path, "/auth/realms/master/protocol/openid-connect/auth"
        )
        self.assertEqual(query_params["scope"][0], "openid bsn")
        self.assertEqual(query_params["client_id"][0], "testclient")
        self.assertEqual(
            query_params["redirect_uri"][0],
            f"http://testserver{reverse('digid_oidc:oidc_authentication_callback')}",
        )

    def test_redirect_with_keycloak_identity_provider_hint(self):
        config = OpenIDConnectPublicConfig.get_solo()
        config.oidc_keycloak_idp_hint = "oidc-digid"
        config.save()

        form = FormFactory.create(authentication_backends=["digid_oidc"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "authentication:start",
            kwargs={"slug": form.slug, "plugin_id": "digid_oidc"},
        )

        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"http://testserver{form_path}?_start=1"

        response = self.client.get(f"{login_url}?next={form_url}")

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = urlparse(response.url)
        query_params = parse_qs(parsed.query)
        self.assertEqual(parsed.hostname, "testserver")
        self.assertEqual(parsed.path, reverse("digid_oidc:oidc_authentication_init"))

        parsed = urlparse(query_params["next"][0])
        query_params = parse_qs(parsed.query)
        self.assertEqual(
            parsed.path,
            reverse(
                "authentication:return",
                kwargs={"slug": form.slug, "plugin_id": "digid_oidc"},
            ),
        )
        self.assertEqual(query_params["next"][0], form_url)

        with requests_mock.Mocker() as m:
            m.head(
                "http://identityprovider/auth/realms/master/protocol/openid-connect/auth",
                status_code=200,
            )
            response = self.client.get(response.url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = urlparse(response.url)
        query_params = parse_qs(parsed.query)
        self.assertEqual(parsed.hostname, "identityprovider")
        self.assertEqual(
            parsed.path, "/auth/realms/master/protocol/openid-connect/auth"
        )
        self.assertEqual(query_params["scope"][0], "openid bsn")
        self.assertEqual(query_params["client_id"][0], "testclient")
        self.assertEqual(
            query_params["redirect_uri"][0],
            f"http://testserver{reverse('digid_oidc:oidc_authentication_callback')}",
        )
        self.assertEqual(query_params["kc_idp_hint"][0], "oidc-digid")
