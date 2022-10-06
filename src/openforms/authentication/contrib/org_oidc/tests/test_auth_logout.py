from unittest.mock import patch

from django.contrib import auth
from django.test import RequestFactory, TestCase

from mozilla_django_oidc_db.models import OpenIDConnectConfig

from openforms.accounts.tests.factories import StaffUserFactory
from openforms.authentication.contrib.org_oidc.backends import OIDCAuthenticationBackend
from openforms.authentication.contrib.org_oidc.plugin import OIDCAuthentication


class PluginLogoutTest(TestCase):
    @patch(
        "mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(),
    )
    def test_logout_empty_session(self, mock_get_solo):
        backend = OIDCAuthenticationBackend()
        user = StaffUserFactory()
        self.client.force_login(user, backend=backend.get_import_path())

        plugin = OIDCAuthentication("org-oidc")

        request = RequestFactory().post("/dummy")
        request.session = self.client.session
        request.user = user

        plugin.logout(request)

        self.assertEqual(list(request.session.keys()), [])
        self.assertFalse(auth.get_user(self.client).is_authenticated)

    @patch(
        "mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(),
    )
    def test_logout_session(self, mock_get_solo):
        backend = OIDCAuthenticationBackend()
        user = StaffUserFactory()
        self.client.force_login(user, backend=backend.get_import_path())

        plugin = OIDCAuthentication("org-oidc")

        session = self.client.session
        session["oidc_id_token"] = "xyz"
        session["oidc_login_next"] = "xyz"
        session["oidc_states"] = "xyz"
        session[plugin.session_key] = "xyz"
        session.save()

        request = RequestFactory().post("/dummy")
        request.session = session
        request.user = user

        plugin.logout(request)

        self.assertEqual(list(request.session.keys()), [])
        self.assertFalse(auth.get_user(self.client).is_authenticated)
