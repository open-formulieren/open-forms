from unittest.mock import patch

from django.test import RequestFactory, TestCase

import requests_mock

from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectEHerkenningConfig,
    OpenIDConnectPublicConfig,
)
from openforms.authentication.contrib.digid_eherkenning_oidc.plugin import (
    DigiDOIDCAuthentication,
    eHerkenningOIDCAuthentication,
)


class PluginLogoutTest(TestCase):
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectPublicConfig.get_solo",
        return_value=OpenIDConnectPublicConfig(
            oidc_op_logout_endpoint="http://foo/logout",
        ),
    )
    @requests_mock.Mocker(real_http=False)
    def test_logout_digid(self, p, mocker):
        mocker.get(
            "http://foo/logout",
            text="ignored",
        )

        plugin = DigiDOIDCAuthentication("digid")

        with self.subTest("empty session"):
            request = RequestFactory().post("/dummy")
            request.session = self.client.session

            plugin.logout(request)

            self.assertEqual(list(request.session.keys()), [])
            self.assertFalse(mocker.called)

        with self.subTest("session"):
            session = self.client.session
            session["oidc_id_token"] = "xyz"
            session["oidc_login_next"] = "xyz"
            session[plugin.session_key] = "xyz"
            session.save()

            request = RequestFactory().post("/dummy")
            request.session = session

            plugin.logout(request)

            self.assertEqual(list(request.session.keys()), [])
            self.assertTrue(mocker.called)

    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo",
        return_value=OpenIDConnectEHerkenningConfig(
            oidc_op_logout_endpoint="http://foo/logout",
        ),
    )
    @requests_mock.Mocker(real_http=False)
    def test_logout_eherkenning(self, p, mocker):
        mocker.get(
            "http://foo/logout",
            text="ignored",
        )

        plugin = eHerkenningOIDCAuthentication("eherkenning")

        with self.subTest("empty session"):
            request = RequestFactory().post("/dummy")
            request.session = self.client.session

            plugin.logout(request)

            self.assertEqual(list(request.session.keys()), [])
            self.assertFalse(mocker.called)

        with self.subTest("session"):
            session = self.client.session
            session["oidc_id_token"] = "xyz"
            session["oidc_login_next"] = "xyz"
            session[plugin.session_key] = "xyz"
            session.save()

            request = RequestFactory().post("/dummy")
            request.session = session

            plugin.logout(request)

            self.assertEqual(list(request.session.keys()), [])
            self.assertTrue(mocker.called)
