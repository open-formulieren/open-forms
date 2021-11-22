from urllib.parse import parse_qs, urlparse

from django.test import TestCase, override_settings
from django.urls import reverse

from rest_framework import status

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)

from ..models import OpenIDConnectEHerkenningConfig


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class eHerkenningOIDCTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = OpenIDConnectEHerkenningConfig.get_solo()
        config.enabled = True
        config.oidc_rp_client_id = "testclient"
        config.oidc_rp_client_secret = "secret"
        config.oidc_rp_sign_algo = "RS256"
        config.oidc_rp_scopes_list = ["openid", "kvk"]
        config.oidc_redirect_allowed_hosts = []

        config.oidc_op_jwks_endpoint = (
            "http://provider.com/auth/realms/master/protocol/openid-connect/certs"
        )
        config.oidc_op_authorization_endpoint = (
            "http://provider.com/auth/realms/master/protocol/openid-connect/auth"
        )
        config.oidc_op_token_endpoint = (
            "http://provider.com/auth/realms/master/protocol/openid-connect/token"
        )
        config.oidc_op_user_endpoint = (
            "http://provider.com/auth/realms/master/protocol/openid-connect/userinfo"
        )
        config.save()

    def test_redirect_to_eherkenning_oidc(self):
        form = FormFactory.create(authentication_backends=["eherkenning_oidc"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "eherkenning_oidc:oidc_authentication_init",
        )

        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"http://testserver{form_path}?_start=1"

        response = self.client.get(f"{login_url}?next={form_url}")

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = urlparse(response.url)
        query_params = parse_qs(parsed.query)

        self.assertEqual(parsed.hostname, "provider.com")
        self.assertEqual(
            parsed.path, "/auth/realms/master/protocol/openid-connect/auth"
        )
        self.assertEqual(query_params["scope"][0], "openid kvk")
        self.assertEqual(query_params["client_id"][0], "testclient")
        self.assertEqual(
            query_params["redirect_uri"][0],
            f"http://testserver{reverse('eherkenning_oidc:oidc_authentication_callback')}",
        )

        self.assertEqual(self.client.session["oidc_login_next"], form_url)

    def test_redirect_to_disallowed_domain(self):
        config = OpenIDConnectEHerkenningConfig().get_solo()
        config.oidc_redirect_allowed_hosts = []
        config.save()

        form = FormFactory.create(authentication_backends=["eherkenning_oidc"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "eherkenning_oidc:oidc_authentication_init",
        )

        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = "http://example.com"

        response = self.client.get(f"{login_url}?next={form_url}")

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_redirect_to_allowed_domain(self):
        config = OpenIDConnectEHerkenningConfig.get_solo()
        config.oidc_redirect_allowed_hosts = ["example.com"]
        config.save()

        form = FormFactory.create(authentication_backends=["eherkenning_oidc"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "eherkenning_oidc:oidc_authentication_init",
        )

        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = "http://example.com"

        response = self.client.get(f"{login_url}?next={form_url}")

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = urlparse(response.url)
        query_params = parse_qs(parsed.query)

        self.assertEqual(parsed.hostname, "provider.com")
        self.assertEqual(
            parsed.path, "/auth/realms/master/protocol/openid-connect/auth"
        )
        self.assertEqual(query_params["scope"][0], "openid kvk")
        self.assertEqual(query_params["client_id"][0], "testclient")
        self.assertEqual(
            query_params["redirect_uri"][0],
            f"http://testserver{reverse('eherkenning_oidc:oidc_authentication_callback')}",
        )

        self.assertEqual(self.client.session["oidc_login_next"], form_url)

    def test_redirect_with_keycloak_identity_provider_hint(self):
        config = OpenIDConnectEHerkenningConfig.get_solo()
        config.oidc_keycloak_idp_hint = "oidc-eHerkenning"
        config.save()

        form = FormFactory.create(authentication_backends=["eherkenning_oidc"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "eherkenning_oidc:oidc_authentication_init",
        )

        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"http://testserver{form_path}?_start=1"

        response = self.client.get(f"{login_url}?next={form_url}")

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

        parsed = urlparse(response.url)
        query_params = parse_qs(parsed.query)

        self.assertEqual(parsed.hostname, "provider.com")
        self.assertEqual(
            parsed.path, "/auth/realms/master/protocol/openid-connect/auth"
        )
        self.assertEqual(query_params["scope"][0], "openid kvk")
        self.assertEqual(query_params["client_id"][0], "testclient")
        self.assertEqual(
            query_params["redirect_uri"][0],
            f"http://testserver{reverse('eherkenning_oidc:oidc_authentication_callback')}",
        )

        # Verify that the Identity provider hint is passed to Keycloak
        self.assertEqual(query_params["kc_idp_hint"][0], "oidc-eHerkenning")

        self.assertEqual(self.client.session["oidc_login_next"], form_url)
