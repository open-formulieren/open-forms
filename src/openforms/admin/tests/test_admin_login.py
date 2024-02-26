"""
Tests for the possible admin login flows.
"""

from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse, reverse_lazy

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from mozilla_django_oidc_db.models import OpenIDConnectConfig

from openforms.accounts.tests.factories import SuperUserFactory

LOGIN_URL = reverse_lazy("admin:login")


@disable_admin_mfa()
@override_settings(USE_OIDC_FOR_ADMIN_LOGIN=False)
class ClassicLoginTests(WebTest):

    def test_admin_login_without_next_param(self):
        user = SuperUserFactory.create()
        login_page = self.app.get(LOGIN_URL, auto_follow=True)

        self.assertEqual(login_page.request.path, reverse("admin-mfa-login"))

        with self.subTest("login flow"):
            form = login_page.forms["login-form"]

            form["auth-username"] = user.username
            form["auth-password"] = "secret"

            admin_index = form.submit().follow()
            self.assertEqual(admin_index.request.path, "/admin/")

    def test_admin_login_with_next_param(self):
        user = SuperUserFactory.create()
        login_page = self.app.get(
            LOGIN_URL, {"next": "/admin/accounts/user/"}, auto_follow=True
        )

        self.assertEqual(login_page.request.path, reverse("admin-mfa-login"))

        with self.subTest("login flow"):
            form = login_page.forms["login-form"]

            form["auth-username"] = user.username
            form["auth-password"] = "secret"

            admin_index = form.submit().follow()
            self.assertEqual(admin_index.request.path, "/admin/accounts/user/")

    def test_admin_login_with_evil_next_param(self):
        user = SuperUserFactory.create()
        login_page = self.app.get(
            LOGIN_URL, {"next": "https://evil.com"}, auto_follow=True
        )

        self.assertEqual(login_page.request.path, reverse("admin-mfa-login"))

        with self.subTest("login flow"):
            form = login_page.forms["login-form"]

            form["auth-username"] = user.username
            form["auth-password"] = "secret"

            admin_index = form.submit().follow()
            self.assertEqual(admin_index.request.path, "/admin/")


@disable_admin_mfa()
@override_settings(USE_OIDC_FOR_ADMIN_LOGIN=True)
class OIDCLoginTests(WebTest):

    def setUp(self):
        super().setUp()

        patcher = patch(
            "mozilla_django_oidc_db.mixins.OpenIDConnectConfig.get_solo",
            return_value=OpenIDConnectConfig(
                enabled=True,
                oidc_op_authorization_endpoint="https://oidc.example.com/",
            ),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_admin_login_without_next_param(self):
        login_page = self.app.get(LOGIN_URL).follow()

        self.assertEqual(login_page.status_code, 302)
        self.assertTrue(
            login_page.headers["Location"].startswith("https://oidc.example.com/")
        )
        self.assertEqual(self.app.session["oidc_login_next"], "/admin/")

    def test_admin_login_with_next_param(self):
        login_page = self.app.get(LOGIN_URL, {"next": "/admin/accounts/user/"}).follow()

        self.assertEqual(login_page.status_code, 302)
        self.assertTrue(
            login_page.headers["Location"].startswith("https://oidc.example.com/")
        )
        self.assertEqual(self.app.session["oidc_login_next"], "/admin/accounts/user/")


@disable_admin_mfa()
class AlreadyLoggedInTests(WebTest):

    def test_admin_login_without_next_param(self):
        user = SuperUserFactory.create()

        login_page = self.app.get(LOGIN_URL, user=user)

        self.assertRedirects(login_page, "/admin/", fetch_redirect_response=False)

    def test_admin_login_with_next_param(self):
        user = SuperUserFactory.create()

        login_page = self.app.get(
            LOGIN_URL, {"next": "/admin/accounts/user/"}, user=user
        )

        self.assertRedirects(
            login_page, "/admin/accounts/user/", fetch_redirect_response=False
        )

    def test_admin_login_with_evil_next_param(self):
        user = SuperUserFactory.create()

        login_page = self.app.get(LOGIN_URL, {"next": "https://evil.com"}, user=user)

        self.assertRedirects(login_page, "/admin/", fetch_redirect_response=False)
