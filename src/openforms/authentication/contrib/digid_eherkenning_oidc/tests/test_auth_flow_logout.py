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

from django.test import override_settings, tag

from django_webtest import DjangoTestApp
from furl import furl
from requests import Session
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory

from openforms.authentication.registry import register as auth_register
from openforms.authentication.tests.utils import URLsHelper
from openforms.contrib.auth_oidc.tests.factories import OFOIDCClientFactory
from openforms.forms.tests.factories import FormFactory
from openforms.utils.tests.keycloak import keycloak_login

from ..plugin import OIDC_ID_TOKEN_SESSION_KEY
from .base import IntegrationTestsBase


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
        plugin = auth_register[plugin_id]
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

    def test_logout_also_logs_out_user_in_openid_provider(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_digid=True)

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

    def test_logout_with_empty_session(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_digid=True)

        assert OIDC_ID_TOKEN_SESSION_KEY not in self.app.session

        # now, initiate the logout, which must trigger the OP logout too
        try:
            self._do_plugin_logout("digid_oidc")
        except Exception as exc:
            raise self.failureException(
                "Logout with empty session unexpectedly crashed"
            ) from exc

    @tag("gh-5095")
    @override_settings(
        ALLOWED_HOSTS=["*"],
        CORS_ALLOWED_ORIGINS=["http://testserver.com"],
    )
    def test_logout_after_form_submission(self):
        """
        if the form has oidc-digid authentication and the user has submitted it
        when they should be automatically logged out from IdP
        """
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_digid=True)
        form = FormFactory.create(authentication_backend="digid_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_oidc")
        # use shared session
        session = Session()
        self.addCleanup(session.close)

        # 1. start authentication in the form
        start_response = self.app.get(start_url)
        redirect_uri = keycloak_login(start_response["Location"], session=session)
        callback_response = self.app.get(redirect_uri, auto_follow=True)
        self.assertEqual(callback_response.request.url, url_helper.frontend_start)
        assert OIDC_ID_TOKEN_SESSION_KEY in self.app.session

        # 2. submit the form
        api_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        # make sure csrf cookie is set
        form_detail_response = self.app.get(api_path)
        body = {
            "form": f"http://testserver.com{api_path}",
            "formUrl": "http://testserver.com/my-form",
        }

        submission_response = self.app.post_json(
            reverse("api:submission-list"),
            body,
            extra_environ={
                "HTTP_X_CSRFTOKEN": form_detail_response.headers["X-CSRFToken"],
            },
        )
        self.assertEqual(submission_response.status_code, 201)

        # 3. complete submission
        response = self.app.post_json(
            reverse(
                "api:submission-complete",
                kwargs={"uuid": submission_response.json["id"]},
            ),
            {"privacy_policy_accepted": True},
            extra_environ={
                "HTTP_X_CSRFTOKEN": form_detail_response.headers["X-CSRFToken"],
            },
        )
        self.assertEqual(response.status_code, 200)

        # assert that the user is logged out
        self.assertNotLoggedInToKeycloak(session, start_url)
        self.assertNotIn(OIDC_ID_TOKEN_SESSION_KEY, self.app.session)


class EHerkenningLogoutTests(LogoutTestsMixin, IntegrationTestsBase):
    """
    Test the (RP-initiated) logout flow for the eHerkenning plugin.
    """

    def test_logout_also_logs_out_user_in_openid_provider(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_eherkenning=True)

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

    def test_logout_with_empty_session(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_eherkenning=True)

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

    def test_logout_also_logs_out_user_in_openid_provider(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_eidas=True)

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

    def test_logout_with_empty_session(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_eidas=True)

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

    def test_logout_also_logs_out_user_in_openid_provider(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True, with_digid_machtigen=True
        )

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

    def test_logout_with_empty_session(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True, with_digid_machtigen=True
        )

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

    def test_logout_also_logs_out_user_in_openid_provider(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True, with_eherkenning_bewindvoering=True
        )

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

    def test_logout_with_empty_session(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True, with_eherkenning_bewindvoering=True
        )

        assert OIDC_ID_TOKEN_SESSION_KEY not in self.app.session

        # now, initiate the logout, which must trigger the OP logout too
        try:
            self._do_plugin_logout("eherkenning_bewindvoering_oidc")
        except Exception as exc:
            raise self.failureException(
                "Logout with empty session unexpectedly crashed"
            ) from exc


class EIDASCompanyLogoutTests(LogoutTestsMixin, IntegrationTestsBase):
    """
    Test the (RP-initiated) logout flow for the eIDAS for companies plugin.
    """

    def test_logout_also_logs_out_user_in_openid_provider(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_eidas_company=True)

        form = FormFactory.create(authentication_backend="eidas_company_oidc")
        start_url = URLsHelper(form=form).get_auth_start(plugin_id="eidas_company_oidc")
        # use shared session to maintain cookie state
        session = Session()
        self.addCleanup(session.close)
        callback_url = self._do_keycloak_login(
            session, start_url, username="eidas-company", password="eidas-company"
        )
        # proceed by completing the login flow
        callback_response = self.app.get(callback_url, auto_follow=True)
        assert callback_response.status_code == 200
        assert OIDC_ID_TOKEN_SESSION_KEY in self.app.session

        # now, initiate the logout, which must trigger the OP logout too
        self._do_plugin_logout("eidas_company_oidc")

        self.assertNotIn(OIDC_ID_TOKEN_SESSION_KEY, self.app.session)
        self.assertNotLoggedInToKeycloak(session, start_url)

    def test_logout_with_empty_session(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_eidas_company=True)

        assert OIDC_ID_TOKEN_SESSION_KEY not in self.app.session

        # now, initiate the logout, which must trigger the OP logout too
        try:
            self._do_plugin_logout("eidas_company_oidc")
        except Exception as exc:
            raise self.failureException(
                "Logout with empty session unexpectedly crashed"
            ) from exc
