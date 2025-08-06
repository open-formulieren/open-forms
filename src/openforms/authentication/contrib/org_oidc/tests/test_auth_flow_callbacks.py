"""
Test the authentication flow for a form.

These tests use VCR. When re-recording, making sure to:

.. code-block:: bash

    cd docker
    docker compose -f docker-compose.keycloak.yml up

to bring up a Keycloak instance.
"""

from django.contrib.auth.models import Group
from django.test import override_settings

from furl import furl
from mozilla_django_oidc_db.registry import register as oidc_register
from mozilla_django_oidc_db.views import OIDCAuthenticationRequestInitView

from openforms.accounts.models import User
from openforms.authentication.constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.authentication.registry import (
    register as auth_register,
)
from openforms.authentication.tests.utils import URLsHelper
from openforms.authentication.views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from openforms.contrib.auth_oidc.tests.factories import (
    OFOIDCClientFactory,
    mock_auth_and_oidc_registers,
)
from openforms.forms.tests.factories import FormFactory
from openforms.utils.tests.keycloak import (
    keycloak_login,
    mock_get_random_string,
)
from openforms.utils.urls import reverse_plus

from ..oidc_plugins.plugins import OIDCOrgPlugin
from ..plugin import OIDCAuthentication
from .base import IntegrationTestsBase


@override_settings(BASE_URL="http://testserver")
class OrgOIDCCallbackTests(IntegrationTestsBase):
    """
    Test the return/callback side after authenticating with the identity provider.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # grab user group (from default_groups fixture)
        assert Group.objects.filter(name__iexact="Registreerders").exists(), (
            "Group with required permissions is missing"
        )

    @mock_get_random_string()
    @mock_auth_and_oidc_registers()
    def test_redirects_after_successful_auth(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True, with_org=True
        )
        oidc_register(oidc_client.identifier)(OIDCOrgPlugin)

        org_init_view = OIDCAuthenticationRequestInitView.as_view(
            identifier=oidc_client.identifier,
            allow_next_from_query=False,
        )

        @auth_register("org-oidc")
        class OFTestAuthPlugin(OIDCAuthentication):
            oidc_plugin_identifier = oidc_client.identifier
            init_view = staticmethod(org_init_view)

        form = FormFactory.create(authentication_backend="org-oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="org-oidc")
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"], username="admin", password="admin"
        )

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        self.assertEqual(callback_response.status_code, 200)
        self.assertTrue(callback_response.context["user"].is_authenticated)

        with self.subTest("redirect state"):
            subject_url = reverse_plus(
                "authentication:registrator-subject",
                kwargs={"slug": form.slug},
                query={"next": url_helper.frontend_start},
            )
            self.assertEqual(callback_response.request.url, subject_url)

        with self.subTest("created user"):
            self.assertEqual(User.objects.count(), 1)
            user = User.objects.get()
            self.assertEqual(user.username, "admin")
            self.assertEqual(user.email, "admin@example.com")
            self.assertEqual(user.employee_id, "9999")

        # check our session data
        self.assertIn(FORM_AUTH_SESSION_KEY, self.app.session)
        s = self.app.session[FORM_AUTH_SESSION_KEY]
        self.assertEqual(s["plugin"], "org-oidc")
        self.assertEqual(s["attribute"], AuthAttribute.employee_id)
        self.assertEqual(s["value"], "9999")

    @mock_get_random_string()
    @mock_auth_and_oidc_registers()
    def test_failing_claim_verification(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_org=True,
            post__options__user_settings__claim_mappings__username=["absent-claim"],
        )
        oidc_register(oidc_client.identifier)(OIDCOrgPlugin)

        org_init_view = OIDCAuthenticationRequestInitView.as_view(
            identifier=oidc_client.identifier,
            allow_next_from_query=False,
        )

        @auth_register("org-oidc")
        class OFTestAuthPlugin(OIDCAuthentication):
            oidc_plugin_identifier = oidc_client.identifier
            init_view = staticmethod(org_init_view)

        form = FormFactory.create(authentication_backend="org-oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="org-oidc")
        start_response = self.app.get(start_url)
        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"], username="admin", password="admin"
        )

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        # XXX: shouldn't this be "digid" so that the correct error message is rendered?
        # Query: ?_digid-message=error
        expected_url = furl(url_helper.frontend_start).add(
            {BACKEND_OUTAGE_RESPONSE_PARAMETER: "org-oidc"}
        )
        self.assertEqual(callback_response.request.url, str(expected_url))
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.app.session)
