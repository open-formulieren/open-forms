"""
Tests for the possible admin login flows.
"""

from django.test import override_settings, tag
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from mozilla_django_oidc_db.constants import OIDC_ADMIN_CONFIG_IDENTIFIER

from openforms.accounts.tests.factories import (
    RecoveryTokenFactory,
    StaffUserFactory,
    SuperUserFactory,
)
from openforms.utils.tests.keycloak import mock_get_random_string, mock_oidc_client

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
    @mock_get_random_string()
    @mock_oidc_client(
        OIDC_ADMIN_CONFIG_IDENTIFIER,
    )
    def test_admin_login_without_next_param(self):
        login_page = self.app.get(LOGIN_URL).follow()

        self.assertEqual(login_page.status_code, 302)
        self.assertTrue(
            login_page.headers["Location"].startswith(
                "http://localhost:8080/realms/test/protocol/openid-connect"
            )
        )
        self.assertEqual(self.app.session["oidc_login_next"], "/admin/")

    @mock_get_random_string()
    @mock_oidc_client(
        OIDC_ADMIN_CONFIG_IDENTIFIER,
    )
    def test_admin_login_with_next_param(self):
        login_page = self.app.get(LOGIN_URL, {"next": "/admin/accounts/user/"}).follow()

        self.assertEqual(login_page.status_code, 302)
        self.assertTrue(
            login_page.headers["Location"].startswith(
                "http://localhost:8080/realms/test/protocol/openid-connect"
            )
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

    @tag("gh-4401")
    def test_non_staff_user(self):
        user = SuperUserFactory.create(is_staff=False)

        login_page = self.app.get(LOGIN_URL, user=user, auto_follow=True)

        self.assertEqual(login_page.status_code, 200)
        self.assertTemplateUsed(login_page, "maykin_2fa/login.html")
        self.assertTemplateUsed(login_page, "admin/login.html")


@override_settings(
    USE_OIDC_FOR_ADMIN_LOGIN=False,
    MAYKIN_2FA_ALLOW_MFA_BYPASS_BACKENDS=[],  # enforce MFA
)
class RecoveryTokenTests(WebTest):
    @tag("gh-4072")
    def test_can_enter_recovery_token(self):
        user = StaffUserFactory.create(
            with_totp_device=True,
            username="admin",
            password="admin",
        )
        recovery_token = RecoveryTokenFactory.create(device__user=user).token
        login_page = self.app.get(LOGIN_URL, auto_follow=True)

        # log in with credentials
        form = login_page.forms["login-form"]
        form["auth-username"] = "admin"
        form["auth-password"] = "admin"
        response = form.submit()

        # we should now be on the enter-your-token page
        form = response.forms["login-form"]
        self.assertIn("token-otp_token", form.fields)

        # do not enter a token, but follow the link to use a recovery token
        link_name = gettext("Use a recovery token")
        recovery_page = response.click(description=link_name)
        self.assertEqual(recovery_page.status_code, 200)

        recovery_form = recovery_page.forms[0]
        recovery_form["backup-otp_token"] = recovery_token
        admin_index = recovery_form.submit().follow()
        self.assertEqual(admin_index.request.path, reverse("admin:index"))
