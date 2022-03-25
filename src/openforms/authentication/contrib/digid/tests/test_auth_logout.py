from django.test import RequestFactory, TestCase

from openforms.authentication.contrib.digid.constants import DIGID_AUTH_SESSION_KEY
from openforms.authentication.contrib.digid.plugin import DigidAuthentication


class PluginLogoutTest(TestCase):
    def test_logout_digid(self):
        plugin = DigidAuthentication("digid")

        with self.subTest("empty session"):
            request = RequestFactory().post("/dummy")
            request.session = self.client.session

            plugin.logout(request)

            self.assertEqual(list(request.session.keys()), [])

        with self.subTest("session"):
            session = self.client.session
            session[DIGID_AUTH_SESSION_KEY] = "xyz"
            session.save()

            request = RequestFactory().post("/dummy")
            request.session = session

            plugin.logout(request)

            self.assertEqual(list(request.session.keys()), [])
