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

from rest_framework.test import APIRequestFactory

from openforms.authentication.registry import register
from openforms.authentication.tests.utils import URLsHelper
from openforms.forms.tests.factories import FormFactory
from openforms.utils.tests.keycloak import (
    keycloak_login,
    mock_get_random_string,
    mock_oidc_client,
)

from ..oidc_plugins.constants import OIDC_ORG_IDENTIFIER
from ..plugin import PLUGIN_IDENTIFIER
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
    @mock_oidc_client(OIDC_ORG_IDENTIFIER)
    def test_logout_clears_session(self):
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
    @mock_oidc_client(OIDC_ORG_IDENTIFIER)
    def test_logout_without_any_session(self):
        self._do_plugin_logout(user=AnonymousUser())

        session = self.app.session
        self.assertEqual(list(session.keys()), [])
        self.assertFalse(auth.get_user(self.app).is_authenticated)  # type: ignore
