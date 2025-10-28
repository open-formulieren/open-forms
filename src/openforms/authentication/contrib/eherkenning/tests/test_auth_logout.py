from django.test import RequestFactory, TestCase

from openforms.authentication.contrib.eherkenning.plugin import (
    EHerkenningAuthentication,
    EIDASAuthentication,
)


class PluginLogoutTest(TestCase):
    def test_logout_eherkenning(self):
        plugin = EHerkenningAuthentication("eherkenning")

        with self.subTest("empty session"):
            request = RequestFactory().post("/dummy")
            request.session = self.client.session

            plugin.logout(request)

            self.assertEqual(list(request.session.keys()), [])

        with self.subTest("session"):
            session = self.client.session
            session[plugin.session_key] = "xyz"  # pyright: ignore[reportAttributeAccessIssue]
            session.save()

            request = RequestFactory().post("/dummy")
            request.session = session

            plugin.logout(request)

            self.assertEqual(list(request.session.keys()), [])

    def test_logout_eidas(self):
        plugin = EIDASAuthentication("eidas")

        with self.subTest("empty session"):
            request = RequestFactory().post("/dummy")
            request.session = self.client.session

            plugin.logout(request)

            self.assertEqual(list(request.session.keys()), [])

        with self.subTest("session"):
            session = self.client.session
            session[plugin.session_key] = "xyz"  # pyright: ignore[reportAttributeAccessIssue]
            session.save()

            request = RequestFactory().post("/dummy")
            request.session = session

            plugin.logout(request)

            self.assertEqual(list(request.session.keys()), [])
