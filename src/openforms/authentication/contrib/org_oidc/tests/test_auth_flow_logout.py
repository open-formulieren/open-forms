"""
Test the authentication flow for a form.

These tests use VCR. When re-recording, making sure to:

.. code-block:: bash

    cd docker
    docker compose -f docker-compose.keycloak.yml up

to bring up a Keycloak instance.
"""

import uuid

from django.contrib import auth
from django.contrib.auth.models import AnonymousUser
from django.test import override_settings

from mozilla_django_oidc_db.registry import register as oidc_register
from mozilla_django_oidc_db.views import OIDCAuthenticationRequestInitView
from rest_framework.test import APIRequestFactory

from openforms.authentication.registry import (
    register,
    register as auth_register,
)
from openforms.authentication.tests.utils import URLsHelper
from openforms.contrib.auth_oidc.tests.factories import (
    OFOIDCClientFactory,
    mock_auth_and_oidc_registers,
)
from openforms.forms.tests.factories import FormFactory
from openforms.utils.tests.keycloak import (
    keycloak_login,
    mock_get_random_string,
)

from ..oidc_plugins.plugins import OIDCOrgPlugin
from ..plugin import PLUGIN_IDENTIFIER, OIDCAuthentication
from .base import IntegrationTestsBase


@override_settings(BASE_URL="http://testserver")
class OrgOIDCCallbackTests(IntegrationTestsBase):
    """
    Test the return/callback side after authenticating with the identity provider.
    """

    def _do_keycloak_login(self, start_url: str) -> None:
        start_response = self.app.get(start_url)
        redirect_uri = keycloak_login(
            start_response["Location"], username="admin", password="admin"
        )
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        assert callback_response.status_code == 200

    def _do_plugin_logout(self, user) -> None:
        request = APIRequestFactory().delete(
            f"/api/v2/authentication/{uuid.uuid4()}/session"
        )
        request.user = user
        request.session = self.app.session  # type: ignore
        plugin = register[PLUGIN_IDENTIFIER]
        plugin.logout(request)
        if not isinstance(request.session, dict):
            request.session.save()

    @mock_get_random_string()
    @mock_auth_and_oidc_registers()
    def test_logout_clears_session(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_org=True,
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

        form = FormFactory.create(authentication_backend=PLUGIN_IDENTIFIER)
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id=PLUGIN_IDENTIFIER)
        self._do_keycloak_login(start_url)
        user = auth.get_user(self.app)  # type: ignore
        self.assertTrue(user.is_authenticated)

        self._do_plugin_logout(user)

        session = self.app.session
        self.assertEqual(list(session.keys()), [])
        self.assertFalse(auth.get_user(self.app).is_authenticated)  # type: ignore

    @mock_get_random_string()
    @mock_auth_and_oidc_registers()
    def test_logout_without_any_session(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_org=True,
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

        self._do_plugin_logout(user=AnonymousUser())

        session = self.app.session
        self.assertEqual(list(session.keys()), [])
        self.assertFalse(auth.get_user(self.app).is_authenticated)  # type: ignore
