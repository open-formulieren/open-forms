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

from openforms.authentication.tests.utils import URLsHelper
from openforms.authentication.views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from openforms.forms.tests.factories import FormFactory

from .base import (
    IntegrationTestsBase,
    mock_digid_config,
    mock_digid_machtigen_config,
    mock_eherkenning_bewindvoering_config,
    mock_eherkenning_config,
    mock_eidas_config,
)


class DigiDInitTests(IntegrationTestsBase):
    """
    Test the outbound part of OIDC-based DigiD authentication.
    """

    CALLBACK_URL = f"http://testserver{reverse_lazy('oidc_authentication_callback')}"

    @mock_digid_config()
    def test_start_flow_redirects_to_oidc_provider(self):
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

    @mock_digid_config(
        oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist"
    )
    def test_idp_availability_check(self):
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

    @mock_digid_config(oidc_keycloak_idp_hint="oidc-digid")
    def test_keycloak_idp_hint_is_respected(self):
        form = FormFactory.create(authentication_backend="digid_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.args["kc_idp_hint"], "oidc-digid")


class EHerkenningInitTests(IntegrationTestsBase):
    """
    Test the outbound part of OIDC-based eHerkenning authentication.
    """

    CALLBACK_URL = f"http://testserver{reverse_lazy('oidc_authentication_callback')}"

    @mock_eherkenning_config()
    def test_start_flow_redirects_to_oidc_provider(self):
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

    @mock_eherkenning_config(
        oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist"
    )
    def test_idp_availability_check(self):
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

    @mock_eherkenning_config(oidc_keycloak_idp_hint="oidc-eherkenning")
    def test_keycloak_idp_hint_is_respected(self):
        form = FormFactory.create(authentication_backend="eherkenning_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eherkenning_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.args["kc_idp_hint"], "oidc-eherkenning")


class EIDASInitTests(IntegrationTestsBase):
    """
    Test the outbound part of OIDC-based eIDAS authentication.
    """

    CALLBACK_URL = f"http://testserver{reverse_lazy('oidc_authentication_callback')}"

    @mock_eidas_config()
    def test_start_flow_redirects_to_oidc_provider(self):
        form = FormFactory.create(authentication_backend="eidas_oidc")
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="eidas_oidc")

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
        self.assertEqual(query_params["scope"], "openid eidas")
        self.assertEqual(query_params["client_id"], "testid")
        self.assertEqual(query_params["redirect_uri"], self.CALLBACK_URL)

    @mock_eidas_config(
        oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist"
    )
    def test_idp_availability_check(self):
        form = FormFactory.create(authentication_backend="eidas_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eidas_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.host, "testserver")
        self.assertEqual(redirect_url.path, url_helper.form_path)
        query_params = redirect_url.query.params
        self.assertEqual(query_params[BACKEND_OUTAGE_RESPONSE_PARAMETER], "eidas_oidc")

    @mock_eidas_config(oidc_keycloak_idp_hint="oidc-eidas")
    def test_keycloak_idp_hint_is_respected(self):
        form = FormFactory.create(authentication_backend="eidas_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eidas_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.args["kc_idp_hint"], "oidc-eidas")


class DigiDMachtigenInitTests(IntegrationTestsBase):
    """
    Test the outbound part of OIDC-based DigiD machtigen authentication.
    """

    CALLBACK_URL = f"http://testserver{reverse_lazy('oidc_authentication_callback')}"

    @mock_digid_machtigen_config()
    def test_start_flow_redirects_to_oidc_provider(self):
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

    @mock_digid_machtigen_config(
        oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist"
    )
    def test_idp_availability_check(self):
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

    @mock_digid_machtigen_config(oidc_keycloak_idp_hint="oidc-digid-machtigen")
    def test_keycloak_idp_hint_is_respected(self):
        form = FormFactory.create(authentication_backend="digid_machtigen_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_machtigen_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.args["kc_idp_hint"], "oidc-digid-machtigen")


class EHerkenningBewindvoeringInitTests(IntegrationTestsBase):
    """
    Test the outbound part of OIDC-based eHerkenning_bewindvoering authentication.
    """

    CALLBACK_URL = f"http://testserver{reverse_lazy('oidc_authentication_callback')}"

    @mock_eherkenning_bewindvoering_config()
    def test_start_flow_redirects_to_oidc_provider(self):
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

    @mock_eherkenning_bewindvoering_config(
        oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist"
    )
    def test_idp_availability_check(self):
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

    @mock_eherkenning_bewindvoering_config(
        oidc_keycloak_idp_hint="oidc-eherkenning-bewindvoering"
    )
    def test_keycloak_idp_hint_is_respected(self):
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
