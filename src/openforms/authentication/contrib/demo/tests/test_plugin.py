from unittest.mock import patch
from urllib.parse import quote

from django.test import RequestFactory, TestCase, override_settings

from openforms.accounts.tests.factories import StaffUserFactory
from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormStepFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ....constants import CO_SIGN_PARAMETER, FORM_AUTH_SESSION_KEY, AuthAttribute
from ....registry import register


@override_settings(CORS_ALLOW_ALL_ORIGINS=True)
class LoginTests(TestCase):
    def test_login_bsn_and_baseclass(self):
        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["demo"],
            form_definition__login_required=True,
        )
        form = step.form
        plugin = register["demo"]
        # demo plugins require staff users, see #1322
        user = StaffUserFactory.create()
        self.client.force_login(user=user)

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
        self.assertRegex(response["content-type"], r"^text/html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")

        url = plugin.get_return_url(request, form)

        # bad without next
        response = self.client.post(url, data={"bsn": "111222333"})
        self.assertRegex(response["content-type"], r"^text/html")
        self.assertEqual(response.content, b"invalid data")
        self.assertEqual(response.status_code, 400)

        # bad without bsn
        response = self.client.post(url, data={"next": "http://foo.bar"})
        self.assertRegex(response["content-type"], r"^text/html")
        self.assertEqual(response.content, b"invalid data")
        self.assertEqual(response.status_code, 400)

        # bad get
        response = self.client.get(url, data={"next": "http://foo.bar"})
        self.assertEqual(response.status_code, 405)

        # good
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.client.session)

        response = self.client.post(
            url, data={"next": "http://foo.bar", "bsn": "111222333"}
        )
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

    def test_login_kvk(self):
        # simplified from above just checking the kvk plugin
        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["demo-kvk"],
            form_definition__login_required=True,
        )
        form = step.form
        plugin = register["demo-kvk"]
        # demo plugins require staff users, see #1322
        user = StaffUserFactory.create()
        self.client.force_login(user=user)

        # we need an arbitrary request
        factory = RequestFactory()
        request = factory.get("/foo")

        url = plugin.get_start_url(request, form)
        next_url = quote("http://foo.bar")

        # start
        response = self.client.get(f"{url}?next={next_url}")
        self.assertRegex(response["content-type"], r"^text/html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")

        # return
        url = plugin.get_return_url(request, form)

        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.client.session)

        response = self.client.post(
            url, data={"next": "http://foo.bar", "kvk": "111222333"}
        )
        self.assertEqual(response.content, b"")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "http://foo.bar")

        self.assertIn(FORM_AUTH_SESSION_KEY, self.client.session)
        self.assertEqual("kvk", self.client.session[FORM_AUTH_SESSION_KEY]["attribute"])
        self.assertEqual(
            "111222333", self.client.session[FORM_AUTH_SESSION_KEY]["value"]
        )


@override_settings(CORS_ALLOW_ALL_ORIGINS=True)
class CoSignLoginAuthenticationTests(SubmissionsMixin, TestCase):
    @patch(
        "openforms.plugins.registry.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(enable_demo_plugins=True),
    )
    def test_login_co_sign_bsn(self, mock_get_solo):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            form__slug="myform",
            form__authentication_backends=["demo"],
        )
        self._add_submission_to_session(submission)
        form = submission.form
        plugin = register["demo"]
        # demo plugins require staff users, see #1322
        user = StaffUserFactory.create()
        self.client.force_login(user=user)
        # we need an arbitrary request
        factory = RequestFactory()
        request = factory.get("/foo")
        start_url = plugin.get_start_url(request, form)
        return_url = plugin.get_return_url(request, form)

        with self.subTest("auth flow start"):
            start_response = self.client.get(
                start_url,
                {"next": "http://localhost:3000", CO_SIGN_PARAMETER: submission.uuid},
            )

            self.assertEqual(start_response.status_code, 200)
            initial_data = start_response.context["form"].initial
            self.assertEqual(
                initial_data,
                {
                    "next": "http://localhost:3000",
                    CO_SIGN_PARAMETER: str(submission.uuid),
                },
            )

        with self.subTest("auth flow invalid data"):
            return_response = self.client.post(
                return_url,
                {
                    "next": "http://localhost:3000",
                    CO_SIGN_PARAMETER: submission.uuid,
                    "bsn": "",
                },
            )

            self.assertEqual(return_response.status_code, 400)

        with self.subTest("auth flow return"):
            return_response = self.client.post(
                return_url,
                {
                    "next": "http://localhost:3000",
                    CO_SIGN_PARAMETER: submission.uuid,
                    "bsn": "111222333",
                },
            )

            self.assertEqual(return_response.status_code, 302)
            self.assertNotIn(FORM_AUTH_SESSION_KEY, self.client.session)
            submission.refresh_from_db()
            self.assertEqual(
                submission.co_sign_data,
                {
                    "plugin": "demo",
                    "representation": "",
                    "identifier": "111222333",
                    "fields": {},
                },
            )
