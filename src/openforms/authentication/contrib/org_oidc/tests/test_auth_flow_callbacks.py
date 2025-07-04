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

from openforms.accounts.models import User
from openforms.forms.tests.factories import FormFactory
from openforms.utils.tests.keycloak import (
    keycloak_login,
    mock_get_random_string,
    mock_oidc_client,
)
from openforms.utils.urls import reverse_plus

from ....constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from ....tests.utils import URLsHelper
from ....views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from ..oidc_plugins.constants import OIDC_ORG_IDENTIFIER
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
    @mock_oidc_client(OIDC_ORG_IDENTIFIER)
    def test_redirects_after_successful_auth(self):
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
    @mock_oidc_client(
        OIDC_ORG_IDENTIFIER,
        overrides={"options.user_settings.claim_mappings.username": ["absent-claim"]},
    )
    def test_failing_claim_verification(self):
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
