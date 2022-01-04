from unittest.mock import patch

from django.test import override_settings
from django.test.client import RequestFactory

from furl import furl
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormStepFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ..constants import CO_SIGN_PARAMETER
from ..registry import Registry
from ..views import (
    BACKEND_OUTAGE_RESPONSE_PARAMETER,
    AuthenticationReturnView,
    AuthenticationStartView,
)
from .mocks import FailingPlugin, Plugin, mock_register


class AuthenticationFlowTests(APITestCase):
    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://foo.bar"]
    )
    def test_standard_authentication_flow(self):
        """
        Assert that a regular login-required-form auth flow works as expected.
        """
        register = Registry()
        register("plugin1")(Plugin)
        plugin = register["plugin1"]

        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["plugin1"],
            form_definition__login_required=True,
        )
        form = step.form

        # we need an arbitrary request
        factory = RequestFactory()
        init_request = factory.get("/foo")

        next_url = "http://foo.bar"
        bad_url = "http://buzz.bazz"

        # check the start view
        url = plugin.get_start_url(init_request, form)

        start_view = AuthenticationStartView.as_view(register=register)

        with self.subTest("start ok"):
            request = factory.get(url, {"next": next_url})
            response = start_view(request, slug=form.slug, plugin_id=plugin.identifier)
            self.assertEqual(response.content, b"start")
            self.assertEqual(response.status_code, 200)

        with self.subTest("start missing next"):
            request = factory.get(url)
            response = start_view(request, slug=form.slug, plugin_id=plugin.identifier)
            self.assertEqual(response.content, b"missing 'next' parameter")
            self.assertEqual(response.status_code, 400)

        with self.subTest("start bad plugin"):
            request = factory.get(url, {"next": next_url})
            response = start_view(request, slug=form.slug, plugin_id="bad_plugin")
            self.assertEqual(response.content, b"unknown plugin")
            self.assertEqual(response.status_code, 400)

        with self.subTest("start bad redirect"):
            request = factory.get(url, {"next": bad_url})
            response = start_view(request, slug=form.slug, plugin_id=plugin.identifier)
            self.assertEqual(response.content, b"redirect not allowed")
            self.assertEqual(response.status_code, 400)

        # check the return view
        url = plugin.get_return_url(request, form)

        return_view = AuthenticationReturnView.as_view(register=register)

        with self.subTest("return ok"):
            request = factory.get(url, {"next": next_url})
            response = return_view(request, slug=form.slug, plugin_id=plugin.identifier)
            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 302)

        with self.subTest("return bad method"):
            request = factory.post(f"{url}?next={next_url}")
            response = return_view(request, slug=form.slug, plugin_id=plugin.identifier)
            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "GET")

        with self.subTest("return bad plugin"):
            request = factory.get(url, {"next": next_url})
            response = return_view(request, slug=form.slug, plugin_id="bad_plugin")
            self.assertEqual(response.content, b"unknown plugin")
            self.assertEqual(response.status_code, 400)

        with self.subTest("return bad redirect"):
            request = factory.get(url, {"next": bad_url})
            response = return_view(request, slug=form.slug, plugin_id=plugin.identifier)
            self.assertEqual(response.content, b"redirect not allowed")
            self.assertEqual(response.status_code, 400)

    @override_settings(CORS_ALLOW_ALL_ORIGINS=True)
    def test_plugin_start_failure_redirects(self):
        register = Registry()
        register("plugin1")(FailingPlugin)
        plugin = register["plugin1"]

        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["plugin1"],
            form_definition__login_required=True,
        )
        form = step.form

        # we need an arbitrary request
        factory = RequestFactory()
        init_request = factory.get("/foo")

        # actual test starts here
        next_url = furl("http://foo.bar?bazz=buzz")
        url = plugin.get_start_url(init_request, form)
        start_view = AuthenticationStartView.as_view(register=register)

        response = start_view(
            factory.get(url, {"next": next_url}),
            slug=form.slug,
            plugin_id="plugin1",
        )

        expected = furl("http://foo.bar?bazz=buzz")
        expected.args[BACKEND_OUTAGE_RESPONSE_PARAMETER] = "plugin1"
        self.assertEqual(furl(response["Location"]), expected)

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    @override_settings(CORS_ALLOW_ALL_ORIGINS=True)
    def test_plugin_start_failure_not_enabled(self, mock_get_solo):
        mock_get_solo.return_value = GlobalConfiguration(
            plugin_configuration={"authentication": {"plugin1": {"enabled": False}}}
        )
        register = Registry()
        register("plugin1")(Plugin)
        plugin = register["plugin1"]

        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["plugin1"],
            form_definition__login_required=True,
        )
        form = step.form

        # we need an arbitrary request
        factory = RequestFactory()
        init_request = factory.get("/foo")

        # actual test starts here
        next_url = furl("http://foo.bar?bazz=buzz")
        url = plugin.get_start_url(init_request, form)
        start_view = AuthenticationStartView.as_view(register=register)
        response = start_view(
            factory.get(url, {"next": next_url}),
            slug=form.slug,
            plugin_id="plugin1",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "authentication plugin not enabled")


@override_settings(CORS_ALLOW_ALL_ORIGINS=True)
class CoSignAuthenticationFlowTests(SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # set up isolated registry instance & register plugin
        register = Registry()
        register("plugin1")(Plugin)

        cls.register = register
        cls.submission = SubmissionFactory.create(
            form__slug="myform",
            form__authentication_backends=["plugin1"],
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            form__formstep__form_definition__slug="stap-1",
        )
        cls.next_url = "https://example.com/f/myform/stap/stap-1"

    @patch("openforms.prefill.signals._add_co_sign_representation")
    def test_co_sign_flow(self, mock_add_co_sign_representation):
        """
        Assert that the authentication flow for co-signing works as expected.
        """
        self._add_submission_to_session(self.submission)

        with mock_register(self.register):
            with self.subTest("start ok"):
                start_url = reverse(
                    "authentication:start",
                    kwargs={"slug": "myform", "plugin_id": "plugin1"},
                )

                response = self.client.get(
                    start_url,
                    {
                        "next": self.next_url,
                        CO_SIGN_PARAMETER: self.submission.uuid,
                    },
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, b"start")

            with self.subTest("return ok"):
                return_url = reverse(
                    "authentication:return",
                    kwargs={"slug": "myform", "plugin_id": "plugin1"},
                )

                response = self.client.get(
                    return_url,
                    {
                        CO_SIGN_PARAMETER: self.submission.uuid,
                        "next": self.next_url,
                    },
                )

                self.assertEqual(response.status_code, 302)

        # validate that the co-sign data is saved on the submission
        self.submission.refresh_from_db()
        self.assertEqual(
            self.submission.co_sign_data,
            {
                "plugin": "plugin1",
                "identifier": "mock-id",
                "representation": "",
                "fields": {
                    "mock_field_1": "field 1",
                    "mock_field_2": "",
                },
            },
        )
        mock_add_co_sign_representation.assert_called_once_with(
            self.submission, "dummy"
        )

    @override_settings(CORS_ALLOW_ALL_ORIGINS=True)
    def test_co_sign_flow_invalid_submission_id(self):
        """
        If the submission ID is not in the session, the co-sign flow must be aborted.
        """
        with mock_register(self.register):
            with self.subTest("start invalid submission"):
                start_url = reverse(
                    "authentication:start",
                    kwargs={"slug": "myform", "plugin_id": "plugin1"},
                )

                response = self.client.get(
                    start_url,
                    {
                        "next": self.next_url,
                        CO_SIGN_PARAMETER: self.submission.uuid,
                    },
                )

                self.assertEqual(response.status_code, 403)

            with self.subTest("return invalid submission"):
                return_url = reverse(
                    "authentication:return",
                    kwargs={"slug": "myform", "plugin_id": "plugin1"},
                )

                response = self.client.get(
                    return_url,
                    {
                        CO_SIGN_PARAMETER: self.submission.uuid,
                        "next": self.next_url,
                    },
                )

                self.assertEqual(response.status_code, 403)

        self.submission.refresh_from_db()
        self.assertEqual(self.submission.co_sign_data, {})
