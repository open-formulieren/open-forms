"""
Test the authentication flow for a form.

These tests use VCR. When re-recording, making sure to:

.. code-block:: bash

    cd docker
    docker compose -f docker-compose.keycloak.yml up

to bring up a Keycloak instance.
"""

from django.urls import reverse_lazy

from furl import furl
from mozilla_django_oidc_db.tests.factories import (
    OIDCProviderFactory,
)
from openforms.utils.tests.keycloak import KEYCLOAK_BASE_URL

from oidc_plugins.constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_DIGID_MACHTIGEN_IDENTIFIER,
    OIDC_EH_BEWINDVOERING_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
)
from openforms.authentication.tests.utils import URLsHelper
from openforms.authentication.views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from openforms.forms.tests.factories import FormFactory
from openforms.utils.tests.keycloak import KeycloakProviderMixin, mock_get_random_string

from .base import (
    IntegrationTestsBase,
    make_client,
)


class DigiDInitTests(KeycloakProviderMixin, IntegrationTestsBase):
    """
    Test the outbound part of OIDC-based DigiD authentication.
    """

    CALLBACK_URL = f"http://testserver{reverse_lazy('oidc_authentication_callback')}"

    @mock_get_random_string()
    def test_start_flow_redirects_to_oidc_provider(self):
        make_client(identifier=OIDC_DIGID_IDENTIFIER, provider=self.provider)

        form = FormFactory.create(authentication_backend="digid_oidc")
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="digid_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_target = furl(response["Location"])
        query_params = redirect_target.query.params
        self.assertEqual(redirect_target.host, "localhost")
        self.assertEqual(redirect_target.port, 8080)
        self.assertEqual(
            redirect_target.path,
            "/realms/test/protocol/openid-connect/auth",
        )
        self.assertEqual(query_params["scope"], "openid bsn")
        self.assertEqual(query_params["client_id"], "testid")
        self.assertEqual(query_params["redirect_uri"], self.CALLBACK_URL)

    @mock_get_random_string()
    def test_idp_availability_check(self):
        bad_provider = OIDCProviderFactory.create(
            identifier="bad-keycloak-provider",
            oidc_op_jwks_endpoint=f"{KEYCLOAK_BASE_URL}/certs",
            oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist",  # Non-existing endpoint!
            oidc_op_token_endpoint=f"{KEYCLOAK_BASE_URL}/token",
            oidc_op_user_endpoint=f"{KEYCLOAK_BASE_URL}/userinfo",
            oidc_op_logout_endpoint=f"{KEYCLOAK_BASE_URL}/logout",
        )

        make_client(
            identifier=OIDC_DIGID_IDENTIFIER,
            provider=bad_provider,
            overrides={"check_op_availability": True},
        )
        form = FormFactory.create(authentication_backend="digid_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.host, "testserver")
        self.assertEqual(redirect_url.path, url_helper.form_path)
        query_params = redirect_url.query.params
        self.assertEqual(query_params[BACKEND_OUTAGE_RESPONSE_PARAMETER], "digid_oidc")

    @mock_get_random_string()
    def test_keycloak_idp_hint_is_respected(self):
        make_client(
            identifier=OIDC_DIGID_IDENTIFIER,
            provider=self.provider,
            overrides={"oidc_keycloak_idp_hint": "oidc-digid"},
        )

        form = FormFactory.create(authentication_backend="digid_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.args["kc_idp_hint"], "oidc-digid")


class EHerkenningInitTests(KeycloakProviderMixin, IntegrationTestsBase):
    """
    Test the outbound part of OIDC-based eHerkenning authentication.
    """

    CALLBACK_URL = f"http://testserver{reverse_lazy('oidc_authentication_callback')}"

    @mock_get_random_string()
    def test_start_flow_redirects_to_oidc_provider(self):
        make_client(identifier=OIDC_EH_IDENTIFIER, provider=self.provider)

        form = FormFactory.create(authentication_backend="eherkenning_oidc")
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="eherkenning_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_target = furl(response["Location"])
        query_params = redirect_target.query.params
        self.assertEqual(redirect_target.host, "localhost")
        self.assertEqual(redirect_target.port, 8080)
        self.assertEqual(
            redirect_target.path,
            "/realms/test/protocol/openid-connect/auth",
        )
        self.assertEqual(query_params["scope"], "openid kvk")
        self.assertEqual(query_params["client_id"], "testid")
        self.assertEqual(query_params["redirect_uri"], self.CALLBACK_URL)

    @mock_get_random_string()
    def test_idp_availability_check(self):
        bad_provider = OIDCProviderFactory.create(
            identifier="bad-keycloak-provider",
            oidc_op_jwks_endpoint=f"{KEYCLOAK_BASE_URL}/certs",
            oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist",  # Non-existing endpoint!
            oidc_op_token_endpoint=f"{KEYCLOAK_BASE_URL}/token",
            oidc_op_user_endpoint=f"{KEYCLOAK_BASE_URL}/userinfo",
            oidc_op_logout_endpoint=f"{KEYCLOAK_BASE_URL}/logout",
        )
        make_client(
            identifier=OIDC_EH_IDENTIFIER,
            provider=bad_provider,
            overrides={"check_op_availability": True},
        )

        form = FormFactory.create(authentication_backend="eherkenning_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eherkenning_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.host, "testserver")
        self.assertEqual(redirect_url.path, url_helper.form_path)
        query_params = redirect_url.query.params
        self.assertEqual(
            query_params[BACKEND_OUTAGE_RESPONSE_PARAMETER], "eherkenning_oidc"
        )

    @mock_get_random_string()
    def test_keycloak_idp_hint_is_respected(self):
        make_client(
            identifier=OIDC_EH_IDENTIFIER,
            provider=self.provider,
            overrides={"oidc_keycloak_idp_hint": "oidc-eherkenning"},
        )

        form = FormFactory.create(authentication_backend="eherkenning_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eherkenning_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.args["kc_idp_hint"], "oidc-eherkenning")


class DigiDMachtigenInitTests(KeycloakProviderMixin, IntegrationTestsBase):
    """
    Test the outbound part of OIDC-based DigiD machtigen authentication.
    """

    CALLBACK_URL = f"http://testserver{reverse_lazy('oidc_authentication_callback')}"

    @mock_get_random_string()
    def test_start_flow_redirects_to_oidc_provider(self):
        make_client(identifier=OIDC_DIGID_MACHTIGEN_IDENTIFIER, provider=self.provider)

        form = FormFactory.create(authentication_backend="digid_machtigen_oidc")
        start_url = URLsHelper(form=form).get_auth_start(
            plugin_id="digid_machtigen_oidc"
        )

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_target = furl(response["Location"])
        query_params = redirect_target.query.params
        self.assertEqual(redirect_target.host, "localhost")
        self.assertEqual(redirect_target.port, 8080)
        self.assertEqual(
            redirect_target.path,
            "/realms/test/protocol/openid-connect/auth",
        )
        self.assertEqual(query_params["scope"], "openid bsn")
        self.assertEqual(query_params["client_id"], "testid")
        self.assertEqual(query_params["redirect_uri"], self.CALLBACK_URL)

    @mock_get_random_string()
    def test_idp_availability_check(self):
        bad_provider = OIDCProviderFactory.create(
            identifier="bad-keycloak-provider",
            oidc_op_jwks_endpoint=f"{KEYCLOAK_BASE_URL}/certs",
            oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist",  # Non-existing endpoint!
            oidc_op_token_endpoint=f"{KEYCLOAK_BASE_URL}/token",
            oidc_op_user_endpoint=f"{KEYCLOAK_BASE_URL}/userinfo",
            oidc_op_logout_endpoint=f"{KEYCLOAK_BASE_URL}/logout",
        )
        make_client(
            identifier=OIDC_DIGID_MACHTIGEN_IDENTIFIER,
            provider=bad_provider,
            overrides={"check_op_availability": True},
        )

        form = FormFactory.create(authentication_backend="digid_machtigen_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_machtigen_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.host, "testserver")
        self.assertEqual(redirect_url.path, url_helper.form_path)
        query_params = redirect_url.query.params
        self.assertEqual(
            query_params[BACKEND_OUTAGE_RESPONSE_PARAMETER], "digid_machtigen_oidc"
        )

    @mock_get_random_string()
    def test_keycloak_idp_hint_is_respected(self):
        make_client(
            identifier=OIDC_DIGID_MACHTIGEN_IDENTIFIER,
            provider=self.provider,
            overrides={"oidc_keycloak_idp_hint": "oidc-digid-machtigen"},
        )

        form = FormFactory.create(authentication_backend="digid_machtigen_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_machtigen_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.args["kc_idp_hint"], "oidc-digid-machtigen")


class EHerkenningBewindvoeringInitTests(KeycloakProviderMixin, IntegrationTestsBase):
    """
    Test the outbound part of OIDC-based eHerkenning_bewindvoering authentication.
    """

    CALLBACK_URL = f"http://testserver{reverse_lazy('oidc_authentication_callback')}"

    @mock_get_random_string()
    def test_start_flow_redirects_to_oidc_provider(self):
        make_client(identifier=OIDC_EH_BEWINDVOERING_IDENTIFIER, provider=self.provider)

        form = FormFactory.create(
            authentication_backend="eherkenning_bewindvoering_oidc"
        )
        start_url = URLsHelper(form=form).get_auth_start(
            plugin_id="eherkenning_bewindvoering_oidc"
        )

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_target = furl(response["Location"])
        query_params = redirect_target.query.params
        self.assertEqual(redirect_target.host, "localhost")
        self.assertEqual(redirect_target.port, 8080)
        self.assertEqual(
            redirect_target.path,
            "/realms/test/protocol/openid-connect/auth",
        )
        self.assertEqual(query_params["scope"], "openid bsn")
        self.assertEqual(query_params["client_id"], "testid")
        self.assertEqual(query_params["redirect_uri"], self.CALLBACK_URL)

    @mock_get_random_string()
    def test_idp_availability_check(self):
        bad_provider = OIDCProviderFactory.create(
            identifier="bad-keycloak-provider",
            oidc_op_jwks_endpoint=f"{KEYCLOAK_BASE_URL}/certs",
            oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist",  # Non-existing endpoint!
            oidc_op_token_endpoint=f"{KEYCLOAK_BASE_URL}/token",
            oidc_op_user_endpoint=f"{KEYCLOAK_BASE_URL}/userinfo",
            oidc_op_logout_endpoint=f"{KEYCLOAK_BASE_URL}/logout",
        )
        make_client(
            identifier=OIDC_EH_BEWINDVOERING_IDENTIFIER,
            provider=bad_provider,
            overrides={"check_op_availability": True},
        )

        form = FormFactory.create(
            authentication_backend="eherkenning_bewindvoering_oidc"
        )
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(
            plugin_id="eherkenning_bewindvoering_oidc"
        )

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.host, "testserver")
        self.assertEqual(redirect_url.path, url_helper.form_path)
        query_params = redirect_url.query.params
        self.assertEqual(
            query_params[BACKEND_OUTAGE_RESPONSE_PARAMETER],
            "eherkenning_bewindvoering_oidc",
        )

    @mock_get_random_string()
    def test_keycloak_idp_hint_is_respected(self):
        make_client(
            identifier=OIDC_EH_BEWINDVOERING_IDENTIFIER,
            provider=self.provider,
            overrides={"oidc_keycloak_idp_hint": "oidc-eherkenning-bewindvoering"},
        )

        form = FormFactory.create(
            authentication_backend="eherkenning_bewindvoering_oidc"
        )
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(
            plugin_id="eherkenning_bewindvoering_oidc"
        )

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(
            redirect_url.args["kc_idp_hint"], "oidc-eherkenning-bewindvoering"
        )
