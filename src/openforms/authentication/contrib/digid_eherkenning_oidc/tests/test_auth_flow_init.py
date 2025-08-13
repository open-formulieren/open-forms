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
from openforms.contrib.auth_oidc.tests.factories import (
    OFOIDCClientFactory,
)
from openforms.forms.tests.factories import FormFactory

from .base import (
    IntegrationTestsBase,
)


class DigiDInitTests(IntegrationTestsBase):
    """
    Test the outbound part of OIDC-based DigiD authentication.
    """

    CALLBACK_URL = f"http://testserver{reverse_lazy('oidc_authentication_callback')}"

    def test_start_flow_redirects_to_oidc_provider(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_digid=True)

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

    def test_idp_availability_check(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid=True,
            oidc_provider__oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist",  # Non-existing endpoint!
            check_op_availability=True,
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

    def test_keycloak_idp_hint_is_respected(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid=True,
            oidc_keycloak_idp_hint="oidc-digid",
        )

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

    def test_start_flow_redirects_to_oidc_provider(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning=True,
        )

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

    def test_idp_availability_check(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning=True,
            oidc_provider__oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist",  # Non-existing endpoint!
            check_op_availability=True,
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

    def test_keycloak_idp_hint_is_respected(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning=True,
            oidc_keycloak_idp_hint="oidc-eherkenning",
        )

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

    def test_start_flow_redirects_to_oidc_provider(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas=True,
        )

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

    def test_idp_availability_check(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas=True,
            oidc_provider__oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist",
            check_op_availability=True,
        )

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

    def test_keycloak_idp_hint_is_respected(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas=True,
            oidc_keycloak_idp_hint="oidc-eidas",
        )

        form = FormFactory.create(authentication_backend="eidas_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eidas_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.args["kc_idp_hint"], "oidc-eidas")


class EIDASCompanyInitTests(IntegrationTestsBase):
    """
    Test the outbound part of OIDC-based eIDAS authentication for companies.
    """

    CALLBACK_URL = f"http://testserver{reverse_lazy('oidc_authentication_callback')}"

    def test_start_flow_redirects_to_oidc_provider(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas_company=True,
        )

        form = FormFactory.create(authentication_backend="eidas_company_oidc")
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="eidas_company_oidc")

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

    def test_idp_availability_check(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas_company=True,
            oidc_provider__oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist",
            check_op_availability=True,
        )

        form = FormFactory.create(authentication_backend="eidas_company_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eidas_company_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.host, "testserver")
        self.assertEqual(redirect_url.path, url_helper.form_path)
        query_params = redirect_url.query.params
        self.assertEqual(
            query_params[BACKEND_OUTAGE_RESPONSE_PARAMETER], "eidas_company_oidc"
        )

    def test_keycloak_idp_hint_is_respected(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas_company=True,
            oidc_keycloak_idp_hint="oidc-eidas",
        )

        form = FormFactory.create(authentication_backend="eidas_company_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eidas_company_oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.args["kc_idp_hint"], "oidc-eidas")


class DigiDMachtigenInitTests(IntegrationTestsBase):
    """
    Test the outbound part of OIDC-based DigiD machtigen authentication.
    """

    CALLBACK_URL = f"http://testserver{reverse_lazy('oidc_authentication_callback')}"

    def test_start_flow_redirects_to_oidc_provider(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid_machtigen=True,
        )

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

    def test_idp_availability_check(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid_machtigen=True,
            oidc_provider__oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist",
            check_op_availability=True,
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

    def test_keycloak_idp_hint_is_respected(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid_machtigen=True,
            oidc_keycloak_idp_hint="oidc-digid-machtigen",
        )

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

    def test_start_flow_redirects_to_oidc_provider(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning_bewindvoering=True,
        )

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

    def test_idp_availability_check(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning_bewindvoering=True,
            oidc_provider__oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist",
            check_op_availability=True,
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

    def test_keycloak_idp_hint_is_respected(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning_bewindvoering=True,
            oidc_keycloak_idp_hint="oidc-eherkenning-bewindvoering",
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
