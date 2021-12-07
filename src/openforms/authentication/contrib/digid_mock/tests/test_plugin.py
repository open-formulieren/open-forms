from unittest.mock import patch
from urllib.parse import quote

from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from furl import furl

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormStepFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ....constants import CO_SIGN_PARAMETER, FORM_AUTH_SESSION_KEY, AuthAttribute
from ....registry import register


@override_settings(CORS_ALLOW_ALL_ORIGINS=True)
class LoginTests(TestCase):
    def test_login(self):
        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["digid-mock"],
            form_definition__login_required=True,
        )
        form = step.form
        plugin = register["digid-mock"]

        # we need an arbitrary request
        factory = RequestFactory()
        request = factory.get("/foo")

        url = plugin.get_start_url(request, form)
        next_url = quote("http://foo.bar")

        # bad without ?next=
        response = self.client.get(url)
        self.assertEqual(response.content, b"missing 'next' parameter")
        self.assertEqual(response.status_code, 400)

        # good
        response = self.client.get(f"{url}?next={next_url}")
        self.assertEqual(response.content, b"")
        self.assertEqual(response.status_code, 302)
        self.assertRegex(response["Location"], r"^http://testserver/digid/")

        url = plugin.get_return_url(request, form)

        # bad without ?next=
        response = self.client.get(url + "?bsn=111222333")
        self.assertEqual(response.content, b"missing 'next' parameter")
        self.assertEqual(response.status_code, 400)

        # bad without ?bsn=
        response = self.client.get(f"{url}?next={next_url}")
        self.assertEqual(response.content, b"missing 'bsn' parameter")
        self.assertEqual(response.status_code, 400)

        # good
        response = self.client.get(url + "?next=http%3A%2F%2Ffoo.bar&bsn=111222333")
        self.assertEqual(response.content, b"")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "http://foo.bar")

        self.assertIn(FORM_AUTH_SESSION_KEY, self.client.session)
        self.assertEqual(
            AuthAttribute.bsn, self.client.session[FORM_AUTH_SESSION_KEY]["attribute"]
        )
        self.assertEqual(
            "111222333", self.client.session[FORM_AUTH_SESSION_KEY]["value"]
        )


@override_settings(CORS_ALLOW_ALL_ORIGINS=True)
class CoSignLoginAuthenticationTests(SubmissionsMixin, TestCase):
    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_login_co_sign_bsn(self, mock_get_solo):
        mock_get_solo.return_value = GlobalConfiguration(enable_demo_plugins=True)
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            form__slug="myform",
            form__authentication_backends=["digid-mock"],
        )
        self._add_submission_to_session(submission)
        form = submission.form
        plugin = register["digid-mock"]
        # we need an arbitrary request
        factory = RequestFactory()
        request = factory.get("/foo")
        acs_url = None

        with self.subTest("auth flow start"):
            start_url = plugin.get_start_url(request, form)

            start_response = self.client.get(
                start_url,
                {"next": "http://localhost:3000", CO_SIGN_PARAMETER: submission.uuid},
            )

            self.assertEqual(start_response.status_code, 302, start_response.content)
            redirect_target = furl(start_response["Location"])
            self.assertEqual(redirect_target.path, reverse("digid-mock:login"))
            acs_url = furl(redirect_target.args["acs"])
            self.assertIn(CO_SIGN_PARAMETER, acs_url.args)
            self.assertEqual(acs_url.args[CO_SIGN_PARAMETER], str(submission.uuid))

        with self.subTest("auth flow no bsn set"):
            if not acs_url:
                self.fail("previous subtest failed")

            # follow the redirect + add the bsn
            acs_url.args["bsn"] = ""
            acs_url.args["next"] = "http://localhost:3000"

            return_response = self.client.get(acs_url)

            self.assertEqual(return_response.status_code, 400)

        with self.subTest("auth flow return"):
            # follow the redirect + add the bsn
            acs_url.args["bsn"] = "111222333"
            acs_url.args["next"] = "http://localhost:3000"

            return_response = self.client.get(acs_url)

            self.assertEqual(return_response.status_code, 302)
            self.assertNotIn(FORM_AUTH_SESSION_KEY, self.client.session)
            submission.refresh_from_db()
            self.assertEqual(
                submission.co_sign_data,
                {"plugin": "digid-mock", "identifier": "111222333", "fields": {}},
            )
