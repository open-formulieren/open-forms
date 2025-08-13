"""
Test the authentication flow for a form.

These tests use VCR. When re-recording, making sure to:

.. code-block:: bash

    cd docker
    docker compose -f docker-compose.keycloak.yml up

to bring up a Keycloak instance.
"""

from django.test import override_settings, tag

import requests
from furl import furl
from rest_framework.reverse import reverse

from openforms.accounts.tests.factories import StaffUserFactory
from openforms.authentication.constants import FORM_AUTH_SESSION_KEY
from openforms.authentication.tests.utils import URLsHelper
from openforms.authentication.views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from openforms.contrib.auth_oidc.tests.factories import OFOIDCClientFactory
from openforms.forms.tests.factories import FormFactory
from openforms.submissions.models import Submission
from openforms.utils.tests.feature_flags import enable_feature_flag
from openforms.utils.tests.keycloak import keycloak_login

from .base import IntegrationTestsBase


class DigiDCallbackTests(IntegrationTestsBase):
    """
    Test the return/callback side after authenticating with the identity provider.
    """

    def test_redirects_after_successful_auth(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_digid=True)

        form = FormFactory.create(authentication_backend="digid_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_oidc")
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(start_response["Location"])

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        self.assertEqual(callback_response.request.url, url_helper.frontend_start)

    def test_successfully_complete_submission(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_digid=True)

        form = FormFactory.create(authentication_backend="digid_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_oidc")
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(start_response["Location"])

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        self.assertEqual(callback_response.request.url, url_helper.frontend_start)

        # assert that we can start a submission
        with (
            self.subTest("submission start"),
            override_settings(
                ALLOWED_HOSTS=["*"],
                CORS_ALLOWED_ORIGINS=["http://testserver.com"],
            ),
        ):
            api_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
            # make sure csrf cookie is set
            form_detail_response = self.app.get(api_path)
            body = {
                "form": f"http://testserver.com{api_path}",
                "formUrl": "http://testserver.com/my-form",
            }

            response = self.app.post_json(
                reverse("api:submission-list"),
                body,
                extra_environ={
                    "HTTP_X_CSRFTOKEN": form_detail_response.headers["X-CSRFToken"],
                },
            )

            self.assertEqual(response.status_code, 201)
            submission = Submission.objects.get()
            self.assertTrue(submission.is_authenticated)

    def test_failing_claim_verification(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid=True,
            options__identity_settings__bsn_claim_path=["absent-claim"],
        )

        form = FormFactory.create(authentication_backend="digid_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_oidc")
        start_response = self.app.get(start_url)
        # simulate login to Keycloak
        redirect_uri = keycloak_login(start_response["Location"])

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        # XXX: shouldn't this be "digid" so that the correct error message is rendered?
        # Query: ?_digid-message=error
        expected_url = furl(url_helper.frontend_start).add(
            {BACKEND_OUTAGE_RESPONSE_PARAMETER: "digid_oidc"}
        )
        self.assertEqual(callback_response.request.url, str(expected_url))
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.app.session)

    @tag("gh-3656", "gh-3692")
    def test_digid_error_reported_for_cancelled_login_anon_django_user(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid=True,
            oidc_rp_scopes_list=["badscope"],
        )

        form = FormFactory.create(authentication_backend="digid_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_oidc")
        # initialize state, but don't actually log in - we have an invalid config and
        # keycloak redirects back to our callback URL with error parameters.
        start_response = self.app.get(start_url)
        auth_response = requests.get(start_response["Location"], allow_redirects=False)
        # check out assumptions/expectations before proceeding
        callback_url = furl(auth_response.headers["Location"])
        assert callback_url.netloc == "testserver"
        assert "state" in callback_url.args
        # modify the error parameters - there doesn't seem to be an obvious way to trigger
        # this via keycloak itself.
        # Note: this is an example of a specific provider. It may differ when a
        # different provider is used. According to
        # https://openid.net/specs/openid-connect-core-1_0.html#AuthError and
        # https://www.rfc-editor.org/rfc/rfc6749.html#section-4.1.2.1 , this is the
        # error we expect from OIDC.
        callback_url.args.update(
            {"error": "access_denied", "error_description": "The user cancelled"}
        )

        callback_response = self.app.get(str(callback_url), auto_follow=True)

        self.assertEqual(callback_response.status_code, 200)
        expected_url = furl(url_helper.frontend_start).add(
            {"_digid-message": "login-cancelled"}
        )
        assert BACKEND_OUTAGE_RESPONSE_PARAMETER not in expected_url.args
        self.assertEqual(callback_response.request.url, str(expected_url))

    @tag("gh-3656", "gh-3692")
    def test_digid_error_reported_for_cancelled_login_with_staff_django_user(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid=True,
            oidc_rp_scopes_list=["badscope"],
        )

        self.app.set_user(StaffUserFactory.create())
        form = FormFactory.create(authentication_backend="digid_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_oidc")
        # initialize state, but don't actually log in - we have an invalid config and
        # keycloak redirects back to our callback URL with error parameters.
        start_response = self.app.get(start_url)
        auth_response = requests.get(start_response["Location"], allow_redirects=False)
        # check out assumptions/expectations before proceeding
        callback_url = furl(auth_response.headers["Location"])
        assert callback_url.netloc == "testserver"
        assert "state" in callback_url.args
        callback_url.args.update(
            {"error": "access_denied", "error_description": "The user cancelled"}
        )

        callback_response = self.app.get(str(callback_url), auto_follow=True)

        self.assertEqual(callback_response.status_code, 200)
        expected_url = furl(url_helper.frontend_start).add(
            {"_digid-message": "login-cancelled"}
        )
        assert BACKEND_OUTAGE_RESPONSE_PARAMETER not in expected_url.args
        self.assertEqual(callback_response.request.url, str(expected_url))


class EHerkenningCallbackTests(IntegrationTestsBase):
    """
    Test the return/callback side after authenticating with the identity provider.
    """

    def test_redirects_after_successful_auth(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_eherkenning=True)

        form = FormFactory.create(authentication_backend="eherkenning_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eherkenning_oidc")
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(start_response["Location"])

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        self.assertEqual(callback_response.request.url, url_helper.frontend_start)

    @tag("gh-4627")
    def test_failure_with_missing_acting_subject_claim(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning=True,
            options__identity_settings__acting_subject_claim_path=["does not exist"],
        )

        form = FormFactory.create(authentication_backend="eherkenning_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eherkenning_oidc")
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(start_response["Location"])

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        self.assertEqual(callback_response.request.url, url_helper.frontend_start)

        # assert that we can start a submission
        with (
            self.subTest("submission start"),
            override_settings(
                ALLOWED_HOSTS=["*"],
                CORS_ALLOWED_ORIGINS=["http://testserver.com"],
            ),
        ):
            api_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
            # make sure csrf cookie is set
            form_detail_response = self.app.get(api_path)
            body = {
                "form": f"http://testserver.com{api_path}",
                "formUrl": "http://testserver.com/my-form",
            }

            response = self.app.post_json(
                reverse("api:submission-list"),
                body,
                extra_environ={
                    "HTTP_X_CSRFTOKEN": form_detail_response.headers["X-CSRFToken"],
                },
            )

            self.assertEqual(response.status_code, 201)
            submission = Submission.objects.get()
            self.assertTrue(submission.is_authenticated)

    @tag("gh-4627")
    @enable_feature_flag("DIGID_EHERKENNING_OIDC_STRICT")
    def test_failure_with_missing_acting_subject_claim_strict_mode(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning=True,
            options__identity_settings__acting_subject_claim_path=["does not exist"],
        )

        form = FormFactory.create(authentication_backend="eherkenning_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eherkenning_oidc")
        start_response = self.app.get(start_url)
        # simulate login to Keycloak
        redirect_uri = keycloak_login(start_response["Location"])

        # complete the login flow on our end
        response = self.app.get(redirect_uri, auto_follow=True)

        self.assertIn("of-auth-problem", response.request.GET)

    def test_failing_claim_verification(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning=True,
            options__identity_settings__legal_subject_claim_path=["does not exist"],
        )

        form = FormFactory.create(authentication_backend="eherkenning_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eherkenning_oidc")
        start_response = self.app.get(start_url)
        # simulate login to Keycloak
        redirect_uri = keycloak_login(start_response["Location"])

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        # XXX: shouldn't this be "eherkenning" so that the correct error message is rendered?
        # Query: ?_eherkenning-message=error
        expected_url = furl(url_helper.frontend_start).add(
            {BACKEND_OUTAGE_RESPONSE_PARAMETER: "eherkenning_oidc"}
        )
        self.assertEqual(callback_response.request.url, str(expected_url))
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.app.session)

    @tag("gh-3656", "gh-3692")
    def test_eherkenning_error_reported_for_cancelled_login_anon_django_user(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning=True,
            oidc_rp_scopes_list=["badscope"],
        )

        form = FormFactory.create(authentication_backend="eherkenning_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eherkenning_oidc")
        # initialize state, but don't actually log in - we have an invalid config and
        # keycloak redirects back to our callback URL with error parameters.
        start_response = self.app.get(start_url)
        auth_response = requests.get(start_response["Location"], allow_redirects=False)
        # check out assumptions/expectations before proceeding
        callback_url = furl(auth_response.headers["Location"])
        assert callback_url.netloc == "testserver"
        assert "state" in callback_url.args
        # modify the error parameters - there doesn't seem to be an obvious way to trigger
        # this via keycloak itself.
        # Note: this is an example of a specific provider. It may differ when a
        # different provider is used. According to
        # https://openid.net/specs/openid-connect-core-1_0.html#AuthError and
        # https://www.rfc-editor.org/rfc/rfc6749.html#section-4.1.2.1 , this is the
        # error we expect from OIDC.
        callback_url.args.update(
            {"error": "access_denied", "error_description": "The user cancelled"}
        )

        callback_response = self.app.get(str(callback_url), auto_follow=True)

        self.assertEqual(callback_response.status_code, 200)
        expected_url = furl(url_helper.frontend_start).add(
            {"_eherkenning-message": "login-cancelled"}
        )
        assert BACKEND_OUTAGE_RESPONSE_PARAMETER not in expected_url.args
        self.assertEqual(callback_response.request.url, str(expected_url))

    @tag("gh-3656", "gh-3692")
    def test_eherkenning_error_reported_for_cancelled_login_with_staff_django_user(
        self,
    ):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning=True,
            oidc_rp_scopes_list=["badscope"],
        )

        self.app.set_user(StaffUserFactory.create())
        form = FormFactory.create(authentication_backend="eherkenning_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eherkenning_oidc")
        # initialize state, but don't actually log in - we have an invalid config and
        # keycloak redirects back to our callback URL with error parameters.
        start_response = self.app.get(start_url)
        auth_response = requests.get(start_response["Location"], allow_redirects=False)
        # check out assumptions/expectations before proceeding
        callback_url = furl(auth_response.headers["Location"])
        assert callback_url.netloc == "testserver"
        assert "state" in callback_url.args
        callback_url.args.update(
            {"error": "access_denied", "error_description": "The user cancelled"}
        )

        callback_response = self.app.get(str(callback_url), auto_follow=True)

        self.assertEqual(callback_response.status_code, 200)
        expected_url = furl(url_helper.frontend_start).add(
            {"_eherkenning-message": "login-cancelled"}
        )
        assert BACKEND_OUTAGE_RESPONSE_PARAMETER not in expected_url.args
        self.assertEqual(callback_response.request.url, str(expected_url))


class EIDASCallbackTests(IntegrationTestsBase):
    """
    Test the return/callback side after authenticating with the identity provider.
    """

    def test_redirects_after_successful_auth(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_eidas=True)

        form = FormFactory.create(authentication_backend="eidas_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eidas_oidc")
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"], username="eidas-person", password="eidas-person"
        )

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        self.assertEqual(callback_response.request.url, url_helper.frontend_start)

    def test_successfully_complete_submission(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_eidas=True)

        form = FormFactory.create(authentication_backend="eidas_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eidas_oidc")
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"], username="eidas-person", password="eidas-person"
        )

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        self.assertEqual(callback_response.request.url, url_helper.frontend_start)

        # assert that we can start a submission
        with (
            self.subTest("submission start"),
            override_settings(
                ALLOWED_HOSTS=["*"],
                CORS_ALLOWED_ORIGINS=["http://testserver.com"],
            ),
        ):
            api_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
            # make sure csrf cookie is set
            form_detail_response = self.app.get(api_path)
            body = {
                "form": f"http://testserver.com{api_path}",
                "formUrl": "http://testserver.com/my-form",
            }

            response = self.app.post_json(
                reverse("api:submission-list"),
                body,
                extra_environ={
                    "HTTP_X_CSRFTOKEN": form_detail_response.headers["X-CSRFToken"],
                },
            )

            self.assertEqual(response.status_code, 201)
            submission = Submission.objects.get()
            self.assertTrue(submission.is_authenticated)

    def test_failing_claim_verification(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas=True,
            options__identity_settings__legal_subject_identifier_claim_path=[
                "absent-claim"
            ],
        )

        form = FormFactory.create(authentication_backend="eidas_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eidas_oidc")
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"], username="eidas-person", password="eidas-person"
        )

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        expected_url = furl(url_helper.frontend_start).add(
            {BACKEND_OUTAGE_RESPONSE_PARAMETER: "eidas_oidc"}
        )
        self.assertIn("of-auth-problem", callback_response.request.GET)
        self.assertEqual(callback_response.request.url, str(expected_url))
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.app.session)

    def test_eidas_error_reported_for_cancelled_login_anon_django_user(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas=True,
            oidc_rp_scopes_list=["badscope"],
        )

        form = FormFactory.create(authentication_backend="eidas_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eidas_oidc")

        # initialize state, but don't actually log in - we have an invalid config and
        # keycloak redirects back to our callback URL with error parameters.
        start_response = self.app.get(start_url)
        auth_response = requests.get(start_response["Location"], allow_redirects=False)

        # check out assumptions/expectations before proceeding
        callback_url = furl(auth_response.headers["Location"])
        assert callback_url.netloc == "testserver"
        assert "state" in callback_url.args

        # modify the error parameters - there doesn't seem to be an obvious way to trigger
        # this via keycloak itself.
        # Note: this is an example of a specific provider. It may differ when a
        # different provider is used. According to
        # https://openid.net/specs/openid-connect-core-1_0.html#AuthError and
        # https://www.rfc-editor.org/rfc/rfc6749.html#section-4.1.2.1 , this is the
        # error we expect from OIDC.
        callback_url.args.update(
            {"error": "access_denied", "error_description": "The user cancelled"}
        )

        callback_response = self.app.get(str(callback_url), auto_follow=True)

        self.assertEqual(callback_response.status_code, 200)
        expected_url = furl(url_helper.frontend_start).add(
            {"_eidas-message": "login-cancelled"}
        )
        assert BACKEND_OUTAGE_RESPONSE_PARAMETER not in expected_url.args
        self.assertEqual(callback_response.request.url, str(expected_url))

    def test_eidas_error_reported_for_cancelled_login_with_staff_django_user(
        self,
    ):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas=True,
            oidc_rp_scopes_list=["badscope"],
        )

        self.app.set_user(StaffUserFactory.create())
        form = FormFactory.create(authentication_backend="eidas_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eidas_oidc")

        # initialize state, but don't actually log in - we have an invalid config and
        # keycloak redirects back to our callback URL with error parameters.
        start_response = self.app.get(start_url)
        auth_response = requests.get(start_response["Location"], allow_redirects=False)

        # check out assumptions/expectations before proceeding
        callback_url = furl(auth_response.headers["Location"])
        assert callback_url.netloc == "testserver"
        assert "state" in callback_url.args
        callback_url.args.update(
            {"error": "access_denied", "error_description": "The user cancelled"}
        )

        callback_response = self.app.get(str(callback_url), auto_follow=True)

        self.assertEqual(callback_response.status_code, 200)
        expected_url = furl(url_helper.frontend_start).add(
            {"_eidas-message": "login-cancelled"}
        )
        assert BACKEND_OUTAGE_RESPONSE_PARAMETER not in expected_url.args
        self.assertEqual(callback_response.request.url, str(expected_url))


class DigiDMachtigenCallbackTests(IntegrationTestsBase):
    """
    Test the return/callback side after authenticating with the identity provider.
    """

    def test_redirects_after_successful_auth(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True, with_digid_machtigen=True
        )

        form = FormFactory.create(authentication_backend="digid_machtigen_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_machtigen_oidc")
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username="digid-machtigen",
            password="digid-machtigen",
        )

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        self.assertEqual(callback_response.request.url, url_helper.frontend_start)

    def test_successfully_complete_submission(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True, with_digid_machtigen=True
        )

        form = FormFactory.create(authentication_backend="digid_machtigen_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_machtigen_oidc")
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username="digid-machtigen",
            password="digid-machtigen",
        )

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        self.assertEqual(callback_response.request.url, url_helper.frontend_start)

        # assert that we can start a submission
        with (
            self.subTest("submission start"),
            override_settings(
                ALLOWED_HOSTS=["*"],
                CORS_ALLOWED_ORIGINS=["http://testserver.com"],
            ),
        ):
            api_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
            # make sure csrf cookie is set
            form_detail_response = self.app.get(api_path)
            body = {
                "form": f"http://testserver.com{api_path}",
                "formUrl": "http://testserver.com/my-form",
            }

            response = self.app.post_json(
                reverse("api:submission-list"),
                body,
                extra_environ={
                    "HTTP_X_CSRFTOKEN": form_detail_response.headers["X-CSRFToken"],
                },
            )

            self.assertEqual(response.status_code, 201)
            submission = Submission.objects.get()
            self.assertTrue(submission.is_authenticated)

    def test_failing_claim_verification(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid_machtigen=True,
            options__identity_settings__representee_bsn_claim_path=["absent-claim"],
            options__identity_settings__authorizee_bsn_claim_path=["absent-claim"],
        )

        form = FormFactory.create(authentication_backend="digid_machtigen_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_machtigen_oidc")
        start_response = self.app.get(start_url)
        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username="digid-machtigen",
            password="digid-machtigen",
        )

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        # XXX: shouldn't this be "digid" so that the correct error message is rendered?
        # Query: ?_digid-message=error
        expected_url = furl(url_helper.frontend_start).add(
            {BACKEND_OUTAGE_RESPONSE_PARAMETER: "digid_machtigen_oidc"}
        )
        self.assertEqual(callback_response.request.url, str(expected_url))
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.app.session)

    @enable_feature_flag("DIGID_EHERKENNING_OIDC_STRICT")
    def test_failing_claim_verification_strict_mode(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid_machtigen=True,
            options__identity_settings__mandate_service_id_claim_path=["absent-claim"],
        )

        form = FormFactory.create(authentication_backend="digid_machtigen_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_machtigen_oidc")
        start_response = self.app.get(start_url)
        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username="digid-machtigen",
            password="digid-machtigen",
        )

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        # XXX: shouldn't this be "digid" so that the correct error message is rendered?
        # Query: ?_digid-message=error
        expected_url = furl(url_helper.frontend_start).add(
            {BACKEND_OUTAGE_RESPONSE_PARAMETER: "digid_machtigen_oidc"}
        )
        self.assertEqual(callback_response.request.url, str(expected_url))
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.app.session)

    @tag("gh-3656", "gh-3692")
    def test_digid_error_reported_for_cancelled_login_anon_django_user(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid_machtigen=True,
            oidc_rp_scopes_list=["badscope"],
        )

        form = FormFactory.create(authentication_backend="digid_machtigen_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_machtigen_oidc")
        # initialize state, but don't actually log in - we have an invalid config and
        # keycloak redirects back to our callback URL with error parameters.
        start_response = self.app.get(start_url)
        auth_response = requests.get(start_response["Location"], allow_redirects=False)
        # check out assumptions/expectations before proceeding
        callback_url = furl(auth_response.headers["Location"])
        assert callback_url.netloc == "testserver"
        assert "state" in callback_url.args
        # modify the error parameters - there doesn't seem to be an obvious way to trigger
        # this via keycloak itself.
        # Note: this is an example of a specific provider. It may differ when a
        # different provider is used. According to
        # https://openid.net/specs/openid-connect-core-1_0.html#AuthError and
        # https://www.rfc-editor.org/rfc/rfc6749.html#section-4.1.2.1 , this is the
        # error we expect from OIDC.
        callback_url.args.update(
            {"error": "access_denied", "error_description": "The user cancelled"}
        )

        callback_response = self.app.get(str(callback_url), auto_follow=True)

        self.assertEqual(callback_response.status_code, 200)
        expected_url = furl(url_helper.frontend_start).add(
            {"_digid-message": "login-cancelled"}
        )
        assert BACKEND_OUTAGE_RESPONSE_PARAMETER not in expected_url.args
        self.assertEqual(callback_response.request.url, str(expected_url))

    @tag("gh-3656", "gh-3692")
    def test_digid_error_reported_for_cancelled_login_with_staff_django_user(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid_machtigen=True,
            oidc_rp_scopes_list=["badscope"],
        )

        self.app.set_user(StaffUserFactory.create())
        form = FormFactory.create(authentication_backend="digid_machtigen_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="digid_machtigen_oidc")
        # initialize state, but don't actually log in - we have an invalid config and
        # keycloak redirects back to our callback URL with error parameters.
        start_response = self.app.get(start_url)
        auth_response = requests.get(start_response["Location"], allow_redirects=False)
        # check out assumptions/expectations before proceeding
        callback_url = furl(auth_response.headers["Location"])
        assert callback_url.netloc == "testserver"
        assert "state" in callback_url.args
        callback_url.args.update(
            {"error": "access_denied", "error_description": "The user cancelled"}
        )

        callback_response = self.app.get(str(callback_url), auto_follow=True)

        self.assertEqual(callback_response.status_code, 200)
        expected_url = furl(url_helper.frontend_start).add(
            {"_digid-message": "login-cancelled"}
        )
        assert BACKEND_OUTAGE_RESPONSE_PARAMETER not in expected_url.args
        self.assertEqual(callback_response.request.url, str(expected_url))


class EHerkenningBewindvoeringCallbackTests(IntegrationTestsBase):
    """
    Test the return/callback side after authenticating with the identity provider.
    """

    def test_redirects_after_successful_auth(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True, with_eherkenning_bewindvoering=True
        )

        form = FormFactory.create(
            authentication_backend="eherkenning_bewindvoering_oidc"
        )
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(
            plugin_id="eherkenning_bewindvoering_oidc"
        )
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username="eherkenning-bewindvoering",
            password="eherkenning-bewindvoering",
        )

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        self.assertEqual(callback_response.request.url, url_helper.frontend_start)

    def test_successfully_complete_submission(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True, with_eherkenning_bewindvoering=True
        )

        form = FormFactory.create(
            authentication_backend="eherkenning_bewindvoering_oidc"
        )
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(
            plugin_id="eherkenning_bewindvoering_oidc"
        )
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username="eherkenning-bewindvoering",
            password="eherkenning-bewindvoering",
        )

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        self.assertEqual(callback_response.request.url, url_helper.frontend_start)

        # assert that we can start a submission
        with (
            self.subTest("submission start"),
            override_settings(
                ALLOWED_HOSTS=["*"],
                CORS_ALLOWED_ORIGINS=["http://testserver.com"],
            ),
        ):
            api_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
            # make sure csrf cookie is set
            form_detail_response = self.app.get(api_path)
            body = {
                "form": f"http://testserver.com{api_path}",
                "formUrl": "http://testserver.com/my-form",
            }

            response = self.app.post_json(
                reverse("api:submission-list"),
                body,
                extra_environ={
                    "HTTP_X_CSRFTOKEN": form_detail_response.headers["X-CSRFToken"],
                },
            )

            self.assertEqual(response.status_code, 201)
            submission = Submission.objects.get()
            self.assertTrue(submission.is_authenticated)

    def test_failing_claim_verification(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning_bewindvoering=True,
            options__identity_settings__legal_subject_claim_path=["absent-claim"],
            options__identity_settings__representee_claim_path=["absent-claim"],
        )

        form = FormFactory.create(
            authentication_backend="eherkenning_bewindvoering_oidc"
        )
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(
            plugin_id="eherkenning_bewindvoering_oidc"
        )
        start_response = self.app.get(start_url)
        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username="eherkenning-bewindvoering",
            password="eherkenning-bewindvoering",
        )

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        # XXX: shouldn't this be "eherkenning" so that the correct error message is rendered?
        # Query: ?_eherkenning-message=error
        expected_url = furl(url_helper.frontend_start).add(
            {BACKEND_OUTAGE_RESPONSE_PARAMETER: "eherkenning_bewindvoering_oidc"}
        )
        self.assertEqual(callback_response.request.url, str(expected_url))
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.app.session)

    @tag("gh-3656", "gh-3692")
    def test_eherkenning_error_reported_for_cancelled_login_anon_django_user(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning_bewindvoering=True,
            oidc_rp_scopes_list=["badscope"],
        )

        form = FormFactory.create(
            authentication_backend="eherkenning_bewindvoering_oidc"
        )
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(
            plugin_id="eherkenning_bewindvoering_oidc"
        )
        # initialize state, but don't actually log in - we have an invalid config and
        # keycloak redirects back to our callback URL with error parameters.
        start_response = self.app.get(start_url)
        auth_response = requests.get(start_response["Location"], allow_redirects=False)
        # check out assumptions/expectations before proceeding
        callback_url = furl(auth_response.headers["Location"])
        assert callback_url.netloc == "testserver"
        assert "state" in callback_url.args
        # modify the error parameters - there doesn't seem to be an obvious way to trigger
        # this via keycloak itself.
        # Note: this is an example of a specific provider. It may differ when a
        # different provider is used. According to
        # https://openid.net/specs/openid-connect-core-1_0.html#AuthError and
        # https://www.rfc-editor.org/rfc/rfc6749.html#section-4.1.2.1 , this is the
        # error we expect from OIDC.
        callback_url.args.update(
            {"error": "access_denied", "error_description": "The user cancelled"}
        )

        callback_response = self.app.get(str(callback_url), auto_follow=True)

        self.assertEqual(callback_response.status_code, 200)
        expected_url = furl(url_helper.frontend_start).add(
            {"_eherkenning-message": "login-cancelled"}
        )
        assert BACKEND_OUTAGE_RESPONSE_PARAMETER not in expected_url.args
        self.assertEqual(callback_response.request.url, str(expected_url))

    @tag("gh-3656", "gh-3692")
    def test_eherkenning_error_reported_for_cancelled_login_with_staff_django_user(
        self,
    ):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning_bewindvoering=True,
            oidc_rp_scopes_list=["badscope"],
        )

        self.app.set_user(StaffUserFactory.create())
        form = FormFactory.create(
            authentication_backend="eherkenning_bewindvoering_oidc"
        )
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(
            plugin_id="eherkenning_bewindvoering_oidc"
        )
        # initialize state, but don't actually log in - we have an invalid config and
        # keycloak redirects back to our callback URL with error parameters.
        start_response = self.app.get(start_url)
        auth_response = requests.get(start_response["Location"], allow_redirects=False)
        # check out assumptions/expectations before proceeding
        callback_url = furl(auth_response.headers["Location"])
        assert callback_url.netloc == "testserver"
        assert "state" in callback_url.args
        callback_url.args.update(
            {"error": "access_denied", "error_description": "The user cancelled"}
        )

        callback_response = self.app.get(str(callback_url), auto_follow=True)

        self.assertEqual(callback_response.status_code, 200)
        expected_url = furl(url_helper.frontend_start).add(
            {"_eherkenning-message": "login-cancelled"}
        )
        assert BACKEND_OUTAGE_RESPONSE_PARAMETER not in expected_url.args
        self.assertEqual(callback_response.request.url, str(expected_url))


class EIDASCompanyCallbackTests(IntegrationTestsBase):
    """
    Test the return/callback side after authenticating with the identity provider.
    """

    def test_redirects_after_successful_auth(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_eidas_company=True)

        form = FormFactory.create(authentication_backend="eidas_company_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eidas_company_oidc")
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username="eidas-company",
            password="eidas-company",
        )

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        self.assertEqual(callback_response.request.url, url_helper.frontend_start)

    def test_successfully_complete_submission(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_eidas_company=True)

        form = FormFactory.create(authentication_backend="eidas_company_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eidas_company_oidc")
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username="eidas-company",
            password="eidas-company",
        )

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        self.assertEqual(callback_response.request.url, url_helper.frontend_start)

        # assert that we can start a submission
        with (
            self.subTest("submission start"),
            override_settings(
                ALLOWED_HOSTS=["*"],
                CORS_ALLOWED_ORIGINS=["http://testserver.com"],
            ),
        ):
            api_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
            # make sure csrf cookie is set
            form_detail_response = self.app.get(api_path)
            body = {
                "form": f"http://testserver.com{api_path}",
                "formUrl": "http://testserver.com/my-form",
            }

            response = self.app.post_json(
                reverse("api:submission-list"),
                body,
                extra_environ={
                    "HTTP_X_CSRFTOKEN": form_detail_response.headers["X-CSRFToken"],
                },
            )

            self.assertEqual(response.status_code, 201)
            submission = Submission.objects.get()
            self.assertTrue(submission.is_authenticated)

    def test_failing_claim_verification(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas_company=True,
            options__identity_settings__legal_subject_identifier_claim_path=[
                "absent-claim"
            ],
        )

        form = FormFactory.create(authentication_backend="eidas_company_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eidas_company_oidc")
        start_response = self.app.get(start_url)

        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username="eidas-company",
            password="eidas-company",
        )

        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)

        expected_url = furl(url_helper.frontend_start).add(
            {BACKEND_OUTAGE_RESPONSE_PARAMETER: "eidas_company_oidc"}
        )
        self.assertIn("of-auth-problem", callback_response.request.GET)
        self.assertEqual(callback_response.request.url, str(expected_url))
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.app.session)

    def test_eidas_company_error_reported_for_cancelled_login_anon_django_user(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas_company=True,
            oidc_rp_scopes_list=["badscope"],
        )

        form = FormFactory.create(authentication_backend="eidas_company_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eidas_company_oidc")

        # initialize state, but don't actually log in - we have an invalid config and
        # keycloak redirects back to our callback URL with error parameters.
        start_response = self.app.get(start_url)
        auth_response = requests.get(start_response["Location"], allow_redirects=False)

        # check out assumptions/expectations before proceeding
        callback_url = furl(auth_response.headers["Location"])
        assert callback_url.netloc == "testserver"
        assert "state" in callback_url.args

        # modify the error parameters - there doesn't seem to be an obvious way to trigger
        # this via keycloak itself.
        # Note: this is an example of a specific provider. It may differ when a
        # different provider is used. According to
        # https://openid.net/specs/openid-connect-core-1_0.html#AuthError and
        # https://www.rfc-editor.org/rfc/rfc6749.html#section-4.1.2.1 , this is the
        # error we expect from OIDC.
        callback_url.args.update(
            {"error": "access_denied", "error_description": "The user cancelled"}
        )

        callback_response = self.app.get(str(callback_url), auto_follow=True)

        self.assertEqual(callback_response.status_code, 200)
        expected_url = furl(url_helper.frontend_start).add(
            {"_eidas-message": "login-cancelled"}
        )
        assert BACKEND_OUTAGE_RESPONSE_PARAMETER not in expected_url.args
        self.assertEqual(callback_response.request.url, str(expected_url))

    def test_eidas_company_error_reported_for_cancelled_login_with_staff_django_user(
        self,
    ):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas_company=True,
            oidc_rp_scopes_list=["badscope"],
        )

        self.app.set_user(StaffUserFactory.create())
        form = FormFactory.create(authentication_backend="eidas_company_oidc")
        url_helper = URLsHelper(form=form)
        start_url = url_helper.get_auth_start(plugin_id="eidas_company_oidc")

        # initialize state, but don't actually log in - we have an invalid config and
        # keycloak redirects back to our callback URL with error parameters.
        start_response = self.app.get(start_url)
        auth_response = requests.get(start_response["Location"], allow_redirects=False)

        # check out assumptions/expectations before proceeding
        callback_url = furl(auth_response.headers["Location"])
        assert callback_url.netloc == "testserver"
        assert "state" in callback_url.args
        callback_url.args.update(
            {"error": "access_denied", "error_description": "The user cancelled"}
        )

        callback_response = self.app.get(str(callback_url), auto_follow=True)

        self.assertEqual(callback_response.status_code, 200)
        expected_url = furl(url_helper.frontend_start).add(
            {"_eidas-message": "login-cancelled"}
        )
        assert BACKEND_OUTAGE_RESPONSE_PARAMETER not in expected_url.args
        self.assertEqual(callback_response.request.url, str(expected_url))
