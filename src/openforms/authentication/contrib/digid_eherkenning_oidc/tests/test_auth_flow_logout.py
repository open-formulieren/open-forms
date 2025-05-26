"""
Test that logouts in our application propagate to the OpenID Connect provider.

See the standard: https://openid.net/specs/openid-connect-rpinitiated-1_0.html#RPLogout,
section '2.  RP-Initiated Logout'.

This is tested against Keycloak, which seems to take some liberties, most notably:

    by redirecting the End-User's User Agent to the OP's Logout Endpoint

KC appears to support logout with an API call too, rather than redirecting the user's
browser to this endpoint.

The specification appears to allow for this though, by providing the `id_token_hint`
parameter. If this is not provided, then section '6. Security considerations' says:

    Logout requests without a valid id_token_hint value are a potential means of denial
    of service; therefore, OPs should obtain explicit confirmation from the End-User
    before acting upon them.

Terms:

Relying Party (RP)
    The application using OpenID Connect, Open Forms in this case.

OpenID Provider (OP)
    The application acting as an identity provider, Keycloak in this case.
"""

import uuid

from django_webtest import DjangoTestApp
from furl import furl
from requests import Session
from rest_framework.test import APIRequestFactory

from openforms.authentication.registry import register
from openforms.authentication.tests.utils import URLsHelper
from openforms.contrib.auth_oidc.plugin import (
    OIDC_ID_TOKEN_SESSION_KEY,
)
from openforms.forms.tests.factories import FormFactory
from openforms.utils.tests.keycloak import keycloak_login

from .base import (
    IntegrationTestsBase,
    mock_digid_config,
    mock_digid_machtigen_config,
    mock_eherkenning_bewindvoering_config,
    mock_eherkenning_config,
    mock_eidas_config,
)


class LogoutTestsMixin:
    app: DjangoTestApp

    def _do_keycloak_login(
        self, session: Session, start_url: str, username: str, password: str
    ) -> str:
        """
        Login to keycloak and capture the callback URL to finish the OIDC flow.
        """
        start_response1 = self.app.get(start_url)
        # login to Keycloak - this sets up a session in keycloak
        redirect_uri1 = keycloak_login(
            start_response1["Location"],
            username=username,
            password=password,
            session=session,
        )
        login_code1 = furl(redirect_uri1).args["code"]
        assert login_code1

        # now hit the auth flow again to verify that we don't need to enter credentials
        # again while still logged in on the OpenID Provider side of things.
        start_response2 = self.app.get(start_url)
        resp = session.get(start_response2["Location"], allow_redirects=False)
        assert resp.status_code == 302
        redirect_uri2 = resp.headers["Location"]
        login_code2 = furl(redirect_uri2).args["code"]
        assert login_code2 and login_code2 != login_code1

        return redirect_uri2

    def _do_plugin_logout(self, plugin_id: str) -> None:
        request = APIRequestFactory().delete(
            f"/api/v2/authentication/{uuid.uuid4()}/session"
        )
        request.session = self.app.session  # type: ignore
        plugin = register[plugin_id]
        plugin.logout(request)
        if not isinstance(request.session, dict):
            request.session.save()

    def assertNotLoggedInToKeycloak(self, session: Session, start_url: str):
        start_response = self.app.get(start_url)
        login_response = session.get(start_response["Location"], allow_redirects=False)
        # presents the login screen again, if we were still logged in, this would be a
        # HTTP 302 redirect to the callback endpoint
        self.assertEqual(login_response.status_code, 200)  # type: ignore


class DigiDLogoutTests(LogoutTestsMixin, IntegrationTestsBase):
    """
    Test the (RP-initiated) logout flow for the DigiD plugin.
    """

    @mock_digid_config()
    def test_logout_also_logs_out_user_in_openid_provider(self):
        form = FormFactory.create(authentication_backend="digid_oidc")
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="digid_oidc")
        # use shared session to maintain cookie state
        session = Session()
        self.addCleanup(session.close)
        callback_url = self._do_keycloak_login(
            session, start_url, username="testuser", password="testuser"
        )
        # proceed by completing the login flow
        callback_response = self.app.get(callback_url, auto_follow=True)
        assert callback_response.status_code == 200
        assert OIDC_ID_TOKEN_SESSION_KEY in self.app.session

        # now, initiate the logout, which must trigger the OP logout too
        self._do_plugin_logout("digid_oidc")

        self.assertNotIn(OIDC_ID_TOKEN_SESSION_KEY, self.app.session)
        self.assertNotLoggedInToKeycloak(session, start_url)

    @mock_digid_config()
    def test_logout_with_empty_session(self):
        assert OIDC_ID_TOKEN_SESSION_KEY not in self.app.session

        # now, initiate the logout, which must trigger the OP logout too
        try:
            self._do_plugin_logout("digid_oidc")
        except Exception as exc:
            raise self.failureException(
                "Logout with empty session unexpectedly crashed"
            ) from exc


class EHerkenningLogoutTests(LogoutTestsMixin, IntegrationTestsBase):
    """
    Test the (RP-initiated) logout flow for the eHerkenning plugin.
    """

    @mock_eherkenning_config()
    def test_logout_also_logs_out_user_in_openid_provider(self):
        form = FormFactory.create(authentication_backend="eherkenning_oidc")
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="eherkenning_oidc")
        # use shared session to maintain cookie state
        session = Session()
        self.addCleanup(session.close)
        callback_url = self._do_keycloak_login(
            session, start_url, username="testuser", password="testuser"
        )
        # proceed by completing the login flow
        callback_response = self.app.get(callback_url, auto_follow=True)
        assert callback_response.status_code == 200
        assert OIDC_ID_TOKEN_SESSION_KEY in self.app.session

        # now, initiate the logout, which must trigger the OP logout too
        self._do_plugin_logout("eherkenning_oidc")

        self.assertNotIn(OIDC_ID_TOKEN_SESSION_KEY, self.app.session)
        self.assertNotLoggedInToKeycloak(session, start_url)

    @mock_eherkenning_config()
    def test_logout_with_empty_session(self):
        assert OIDC_ID_TOKEN_SESSION_KEY not in self.app.session

        # now, initiate the logout, which must trigger the OP logout too
        try:
            self._do_plugin_logout("eherkenning_oidc")
        except Exception as exc:
            raise self.failureException(
                "Logout with empty session unexpectedly crashed"
            ) from exc


class EIDASLogoutTests(LogoutTestsMixin, IntegrationTestsBase):
    """
    Test the (RP-initiated) logout flow for the eIDAS plugin.
    """

    @mock_eidas_config()
    def test_logout_also_logs_out_user_in_openid_provider(self):
        form = FormFactory.create(authentication_backend="eidas_oidc")
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="eidas_oidc")
        # use shared session to maintain cookie state
        session = Session()
        self.addCleanup(session.close)
        callback_url = self._do_keycloak_login(
            session, start_url, username="eidas-person", password="eidas-person"
        )
        # proceed by completing the login flow
        callback_response = self.app.get(callback_url, auto_follow=True)
        assert callback_response.status_code == 200
        assert OIDC_ID_TOKEN_SESSION_KEY in self.app.session

        # now, initiate the logout, which must trigger the OP logout too
        self._do_plugin_logout("eidas_oidc")

        self.assertNotIn(OIDC_ID_TOKEN_SESSION_KEY, self.app.session)
        self.assertNotLoggedInToKeycloak(session, start_url)

    @mock_eidas_config()
    def test_logout_with_empty_session(self):
        assert OIDC_ID_TOKEN_SESSION_KEY not in self.app.session

        # now, initiate the logout, which must trigger the OP logout too
        try:
            self._do_plugin_logout("eidas_oidc")
        except Exception as exc:
            raise self.failureException(
                "Logout with empty session unexpectedly crashed"
            ) from exc


class DigiDMachtigenLogoutTests(LogoutTestsMixin, IntegrationTestsBase):
    """
    Test the (RP-initiated) logout flow for the DigiD Nachtigen plugin.
    """

    @mock_digid_machtigen_config()
    def test_logout_also_logs_out_user_in_openid_provider(self):
        form = FormFactory.create(authentication_backend="digid_machtigen_oidc")
        start_url = URLsHelper(form=form).get_auth_start(
            plugin_id="digid_machtigen_oidc"
        )
        # use shared session to maintain cookie state
        session = Session()
        self.addCleanup(session.close)
        callback_url = self._do_keycloak_login(
            session, start_url, username="digid-machtigen", password="digid-machtigen"
        )
        # proceed by completing the login flow
        callback_response = self.app.get(callback_url, auto_follow=True)
        assert callback_response.status_code == 200
        assert OIDC_ID_TOKEN_SESSION_KEY in self.app.session

        # now, initiate the logout, which must trigger the OP logout too
        self._do_plugin_logout("digid_machtigen_oidc")

        self.assertNotIn(OIDC_ID_TOKEN_SESSION_KEY, self.app.session)
        self.assertNotLoggedInToKeycloak(session, start_url)

    @mock_digid_machtigen_config()
    def test_logout_with_empty_session(self):
        assert OIDC_ID_TOKEN_SESSION_KEY not in self.app.session

        # now, initiate the logout, which must trigger the OP logout too
        try:
            self._do_plugin_logout("digid_machtigen_oidc")
        except Exception as exc:
            raise self.failureException(
                "Logout with empty session unexpectedly crashed"
            ) from exc


class EHerkenningBewindvoeringLogoutTests(LogoutTestsMixin, IntegrationTestsBase):
    """
    Test the (RP-initiated) logout flow for the eHerkenning Bewindvoering plugin.
    """

    @mock_eherkenning_bewindvoering_config()
    def test_logout_also_logs_out_user_in_openid_provider(self):
        form = FormFactory.create(
            authentication_backend="eherkenning_bewindvoering_oidc"
        )
        start_url = URLsHelper(form=form).get_auth_start(
            plugin_id="eherkenning_bewindvoering_oidc"
        )
        # use shared session to maintain cookie state
        session = Session()
        self.addCleanup(session.close)
        callback_url = self._do_keycloak_login(
            session,
            start_url,
            username="eherkenning-bewindvoering",
            password="eherkenning-bewindvoering",
        )
        # proceed by completing the login flow
        callback_response = self.app.get(callback_url, auto_follow=True)
        assert callback_response.status_code == 200
        assert OIDC_ID_TOKEN_SESSION_KEY in self.app.session

        # now, initiate the logout, which must trigger the OP logout too
        self._do_plugin_logout("eherkenning_bewindvoering_oidc")

        self.assertNotIn(OIDC_ID_TOKEN_SESSION_KEY, self.app.session)
        self.assertNotLoggedInToKeycloak(session, start_url)

    @mock_eherkenning_bewindvoering_config()
    def test_logout_with_empty_session(self):
        assert OIDC_ID_TOKEN_SESSION_KEY not in self.app.session

        # now, initiate the logout, which must trigger the OP logout too
        try:
            self._do_plugin_logout("eherkenning_bewindvoering_oidc")
        except Exception as exc:
            raise self.failureException(
                "Logout with empty session unexpectedly crashed"
            ) from exc
