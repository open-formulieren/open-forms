"""
Test authentication to the admin with OpenID Connect.

Some of hese tests use VCR. When re-recording, making sure to:

.. code-block:: bash

    cd docker
    docker compose -f docker-compose.keycloak.yml up

to bring up a Keycloak instance.
"""

from pathlib import Path

from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from mozilla_django_oidc_db.models import OIDCClient

from openforms.contrib.auth_oidc.tests.factories import (
    OFOIDCClientFactory,
)
from openforms.utils.tests.keycloak import keycloak_login
from openforms.utils.tests.oidc import OIDCMixin
from openforms.utils.tests.vcr import OFVCRMixin

from ..models import User
from .factories import StaffUserFactory

TEST_FILES = (Path(__file__).parent / "data").resolve()


class OIDCLoginButtonTestCase(OIDCMixin, WebTest):
    def test_oidc_button_disabled(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True, with_admin=True, enabled=False
        )

        response = self.app.get(reverse("admin-mfa-login"))

        oidc_login_link = response.html.find(
            "a", string=_("Login with organization account")
        )
        # Verify that the login button is not visible
        self.assertIsNone(oidc_login_link)

    def test_oidc_button_enabled(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True, with_admin=True, enabled=True
        )

        response = self.app.get(reverse("admin-mfa-login"))

        oidc_login_link = response.html.find(
            "a", string=_("Login with organization account")
        )
        # Verify that the login button is visible
        self.assertIsNotNone(oidc_login_link)
        self.assertEqual(
            oidc_login_link.attrs["href"], reverse("oidc_authentication_init")
        )

    def test_config_not_found(self):
        assert not OIDCClient.objects.exists()

        response = self.app.get(reverse("admin-mfa-login"))

        self.assertEqual(response.status_code, 200)
        oidc_login_link = response.html.find(
            "a", string=_("Login with organization account")
        )
        # Verify that the login button is not visible
        self.assertIsNone(oidc_login_link)


class OIDCFlowTests(OIDCMixin, OFVCRMixin, WebTest):
    VCR_TEST_FILES = TEST_FILES

    def test_duplicate_email_unique_constraint_violated(self):
        """
        Assert that duplicate email addresses result in usable user feedback.

        Regression test for #1199
        """
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_admin=True,
            enabled=True,
            options__user_settings__claim_mappings__email=["email"],
        )
        # this user collides on the email address
        staff_user = StaffUserFactory.create(
            username="no-match", email="admin@example.com"
        )
        login_page = self.app.get(reverse("admin-mfa-login"))
        start_response = login_page.click(
            description=_("Login with organization account")
        )
        assert start_response.status_code == 302
        redirect_uri = keycloak_login(
            start_response["Location"], username="admin", password="admin"
        )

        error_page = self.app.get(redirect_uri, auto_follow=True)

        with self.subTest("error page"):
            self.assertEqual(error_page.status_code, 200)
            self.assertEqual(error_page.request.path, reverse("admin-oidc-error"))
            self.assertEqual(
                error_page.context["oidc_error"],
                'duplicate key value violates unique constraint "filled_email_unique"'
                "\nDETAIL:  Key (email)=(admin@example.com) already exists.",
            )
            self.assertContains(
                error_page, "duplicate key value violates unique constraint"
            )

        with self.subTest("user state unmodified"):
            self.assertEqual(User.objects.count(), 1)
            staff_user.refresh_from_db()
            self.assertEqual(staff_user.username, "no-match")
            self.assertEqual(staff_user.email, "admin@example.com")
            self.assertTrue(staff_user.is_staff)

    def test_happy_flow(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_admin=True,
            enabled=True,
            options__user_settings__claim_mappings__username=["preferred_username"],
            options__groups_settings__make_users_staff=True,
        )
        login_page = self.app.get(reverse("admin-mfa-login"))
        start_response = login_page.click(
            description=_("Login with organization account")
        )
        assert start_response.status_code == 302

        redirect_uri = keycloak_login(
            start_response["Location"], username="admin", password="admin"
        )

        admin_index = self.app.get(redirect_uri, auto_follow=True)

        self.assertEqual(admin_index.status_code, 200)
        self.assertEqual(admin_index.request.path, reverse("admin:index"))

        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get()
        self.assertEqual(user.username, "admin")

    def test_happy_flow_existing_user(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_admin=True,
            enabled=True,
            options__user_settings__claim_mappings__username=["preferred_username"],
            options__user_settings__claim_mappings__email=["email"],
            options__groups_settings__make_users_staff=False,
        )

        staff_user = StaffUserFactory.create(username="admin", email="update-me")
        login_page = self.app.get(reverse("admin-mfa-login"))
        start_response = login_page.click(
            description=_("Login with organization account")
        )
        assert start_response.status_code == 302
        redirect_uri = keycloak_login(
            start_response["Location"], username="admin", password="admin"
        )

        admin_index = self.app.get(redirect_uri, auto_follow=True)

        self.assertEqual(admin_index.status_code, 200)
        self.assertEqual(admin_index.request.path, reverse("admin:index"))

        self.assertEqual(User.objects.count(), 1)
        staff_user.refresh_from_db()
        self.assertEqual(staff_user.username, "admin")
        self.assertEqual(staff_user.email, "admin@example.com")
