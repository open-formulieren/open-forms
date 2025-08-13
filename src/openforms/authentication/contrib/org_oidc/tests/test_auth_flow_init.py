"""
Test the authentication flow for a form.

These tests use VCR. When re-recording, making sure to:

.. code-block:: bash

    cd docker
    docker compose -f docker-compose.keycloak.yml up

to bring up a Keycloak instance.
"""

from django.contrib.auth import get_user
from django.urls import reverse, reverse_lazy

from furl import furl

from openforms.accounts.tests.factories import StaffUserFactory
from openforms.authentication.tests.utils import URLsHelper
from openforms.authentication.views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from openforms.contrib.auth_oidc.tests.factories import OFOIDCClientFactory
from openforms.forms.tests.factories import FormFactory

from .base import IntegrationTestsBase


class OrgOIDCInitTests(IntegrationTestsBase):
    """
    Test the outbound part of OIDC-based organisation user authentication.
    """

    CALLBACK_URL = f"http://testserver{reverse_lazy('oidc_authentication_callback')}"

    def test_start_flow_redirects_to_oidc_provider(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_org=True)
        form = FormFactory.create(authentication_backend="org-oidc")
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="org-oidc")

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
        self.assertEqual(query_params["scope"], "openid email profile employeeId")
        self.assertEqual(query_params["client_id"], "testid")
        self.assertEqual(query_params["redirect_uri"], self.CALLBACK_URL)

    def test_idp_availability_check(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_org=True,
            oidc_provider__oidc_op_authorization_endpoint="http://localhost:8080/i-dont-exist",
            check_op_availability=True,
        )
        form = FormFactory.create(authentication_backend="org-oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="org-oidc")

        response = self.app.get(start_url)

        self.assertEqual(response.status_code, 302)
        redirect_url = furl(response["Location"])
        self.assertEqual(redirect_url.host, "testserver")
        self.assertEqual(redirect_url.path, url_helper.form_path)
        query_params = redirect_url.query.params
        self.assertEqual(query_params[BACKEND_OUTAGE_RESPONSE_PARAMETER], "org-oidc")

    def test_start_flow_logs_out_existing_user(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_org=True)
        user = StaffUserFactory.create()
        self.app.get(reverse("admin:index"), user=user)
        form = FormFactory.create(authentication_backend="org-oidc")
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="org-oidc")
        with self.subTest("verify auth state before test"):
            user = get_user(self.app)  # type: ignore
            self.assertTrue(user.is_authenticated)
            self.assertFalse(user.is_anonymous)

        self.app.get(start_url)

        user = get_user(self.app)  # type: ignore
        self.assertFalse(user.is_authenticated)
        self.assertTrue(user.is_anonymous)
