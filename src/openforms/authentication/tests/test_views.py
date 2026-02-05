from unittest.mock import patch

from django.contrib.sessions.backends.base import SessionBase
from django.test import TestCase, override_settings, tag
from django.test.client import RequestFactory
from django.utils.translation import gettext as _

from django_webtest import WebTest
from furl import furl
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.config.models import GlobalConfiguration
from openforms.config.tests.factories import ThemeFactory
from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ..constants import (
    CO_SIGN_PARAMETER,
    FORM_AUTH_SESSION_KEY,
    REGISTRATOR_SUBJECT_SESSION_KEY,
    AuthAttribute,
)
from ..registry import Registry
from ..views import (
    BACKEND_OUTAGE_RESPONSE_PARAMETER,
    AuthenticationReturnView,
    AuthenticationStartView,
)
from .mocks import (
    BadConfigurationOptionsPlugin,
    FailingPlugin,
    Plugin,
    RequiresAdminPlugin,
    mock_register,
)


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
        register("plugin2")(Plugin)
        plugin = register["plugin1"]

        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backend="plugin1",
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

        with self.subTest("start bad authentication backend"):
            request = factory.get(url, {"next": next_url})
            request.session = SessionBase()
            response = start_view(request, slug=form.slug, plugin_id="plugin2")
            self.assertEqual(response.content, b"plugin not allowed")
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

        with self.subTest("return bad authentication backend"):
            request = factory.get(url, {"next": next_url})
            request.session = SessionBase()
            response = return_view(request, slug=form.slug, plugin_id="plugin2")
            self.assertEqual(response.content, b"plugin not allowed")
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
            form__authentication_backend="plugin1",
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
            factory.get(url, {"next": str(next_url)}),
            slug=form.slug,
            plugin_id="plugin1",
        )

        expected = furl("http://foo.bar?bazz=buzz")
        expected.args[BACKEND_OUTAGE_RESPONSE_PARAMETER] = "plugin1"
        self.assertEqual(furl(response["Location"]), expected)

    @override_settings(CORS_ALLOW_ALL_ORIGINS=True)
    def test_plugin_bad_configuration_options(self):
        register = Registry()
        register("plugin1")(BadConfigurationOptionsPlugin)
        plugin = register["plugin1"]

        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backend="plugin1",
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
            factory.get(url, {"next": str(next_url)}),
            slug=form.slug,
            plugin_id="plugin1",
        )

        expected = furl("http://foo.bar?bazz=buzz")
        expected.args[BACKEND_OUTAGE_RESPONSE_PARAMETER] = "plugin1"
        self.assertEqual(furl(response["Location"]), expected)

    @patch("openforms.plugins.plugin.GlobalConfiguration.get_solo")
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
            form__authentication_backend="plugin1",
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
            factory.get(url, {"next": str(next_url)}),
            slug=form.slug,
            plugin_id="plugin1",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "authentication plugin not enabled")

    @override_settings(CORS_ALLOW_ALL_ORIGINS=True)
    def test_plugin_admin_required_not_logged_in(self):
        register = Registry()
        register("plugin1")(RequiresAdminPlugin)
        FormFactory.create(
            generate_minimal_setup=True,
            slug="myform",
            authentication_backend="plugin1",
            formstep__form_definition__login_required=True,
        )

        # go through the full client to simulate actual sessions
        start_url = reverse(
            "authentication:start",
            kwargs={"slug": "myform", "plugin_id": "plugin1"},
        )

        with mock_register(register):
            response = self.client.get(
                start_url, {"next": "https://example.com/f/myform/stap/stap-1"}
            )

        self.assertEqual(response.status_code, 403)

    @override_settings(CORS_ALLOW_ALL_ORIGINS=True)
    def test_plugin_admin_required_users_logged_in(self):
        register = Registry()
        register("plugin1")(RequiresAdminPlugin)
        FormFactory.create(
            generate_minimal_setup=True,
            slug="myform",
            authentication_backend="plugin1",
            formstep__form_definition__login_required=True,
        )

        # go through the full client to simulate actual sessions
        start_url = reverse(
            "authentication:start",
            kwargs={"slug": "myform", "plugin_id": "plugin1"},
        )

        expected = (
            (UserFactory.create(), 403),
            (StaffUserFactory.create(), 200),
        )

        with mock_register(register):
            for user, expected_status in expected:
                with self.subTest(is_staff=user.is_staff):
                    self.client.force_authenticate(user)

                    response = self.client.get(
                        start_url, {"next": "https://example.com/f/myform/stap/stap-1"}
                    )

                    self.assertEqual(response.status_code, expected_status)

    @override_settings(CORS_ALLOW_ALL_ORIGINS=True)
    def test_plugin_admin_required_return_flow(self):
        register = Registry()
        register("plugin1")(RequiresAdminPlugin)
        FormFactory.create(
            generate_minimal_setup=True,
            slug="myform",
            authentication_backend="plugin1",
            formstep__form_definition__login_required=True,
        )
        # go through the full client to simulate actual sessions
        return_url = reverse(
            "authentication:return",
            kwargs={"slug": "myform", "plugin_id": "plugin1"},
        )

        expected = (
            (None, 403),
            (UserFactory.create(), 403),
            (StaffUserFactory.create(), 302),
        )

        with mock_register(register):
            for user, expected_status in expected:
                with self.subTest(is_staff=user.is_staff if user else "anon"):
                    self.client.force_authenticate(user=user)

                    response = self.client.get(
                        return_url, {"next": "https://example.com/f/myform/stap/stap-1"}
                    )

                    self.assertEqual(response.status_code, expected_status)


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
            form__authentication_backend="plugin1",
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
                "version": "v1",
                "plugin": "plugin1",
                "identifier": "mock-id",
                "representation": "",
                "co_sign_auth_attribute": "bsn",
                "fields": {
                    "mock_field_1": "field 1",
                    "mock_field_2": "",
                },
            },
        )
        mock_add_co_sign_representation.assert_called_once_with(self.submission, "bsn")

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


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://testserver"]
)
class RegistratorSubjectInfoViewTests(WebTest):
    csrf_checks = False

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.form = FormStepFactory(
            form__slug="myform",
            form__authentication_backend="plugin1",
            form_definition__login_required=True,
        ).form

        form_path = reverse("core:form-detail", kwargs={"slug": cls.form.slug})
        cls.form_url = f"http://testserver{form_path}"

        f = furl(
            reverse(
                "authentication:registrator-subject",
                kwargs={"slug": cls.form.slug},
            )
        )
        cls.subject_url_missing_next = f.url

        f.args["next"] = "http://not-in-whitelist.net/foo"
        cls.subject_url_not_allowed_next = f.url

        f.args["next"] = cls.form_url
        cls.subject_url = f.url

        cls.user = UserFactory(
            user_permissions=["of_authentication.can_register_customer_submission"]
        )

    def test_view_requires_logged_in_user(self):
        with self.subTest("403 without user"):
            self.app.get(self.subject_url, status=status.HTTP_403_FORBIDDEN)
        with self.subTest("200 with user"):
            self.app.get(self.subject_url, status=200, user=self.user)

    def test_view_requires_permissions(self):
        with self.subTest("200 with user and permission"):
            self.app.get(self.subject_url, status=200, user=self.user)
        with self.subTest("403 with new user and no permission"):
            self.app.get(
                self.subject_url, status=status.HTTP_403_FORBIDDEN, user=UserFactory()
            )

    def test_view_displays_user(self):
        response = self.app.get(self.subject_url, status=200, user=self.user)
        self.assertContains(response, self.user.get_employee_name())

    @tag("gh-4313")
    def test_view_loads_theme(self):
        theme = ThemeFactory.create(
            design_token_values={
                "of": {
                    "color": {
                        "bg": {"value": "#FFF"},
                    },
                    "layout": {"bg": {"value": "#FFF"}},
                    "typography": {"sans-serif": {"font-family": {"value": "Lexend"}}},
                },
            },
            logo="somefile.svg",
        )
        self.form.theme = theme
        self.form.save()

        response = self.app.get(self.subject_url, status=200, user=self.user)
        self.assertContains(response, self.user.get_employee_name())

        style = response.pyquery.find("style")

        self.assertIsNotNone(style)

        expected = (
            ".openforms-theme { --of-color-bg: #FFF; --of-layout-bg: #FFF; "
            "--of-typography-sans-serif-font-family: Lexend; --of-header-logo-url: url('/media/somefile.svg'); }"
        )
        self.assertEqual(style.text(), expected)

    def test_view_requires_redirect_target(self):
        with self.subTest("get"):
            self.app.get(
                self.subject_url_missing_next,
                status=status.HTTP_400_BAD_REQUEST,
                user=self.user,
            )
        with self.subTest("post"):
            self.app.post(
                self.subject_url_missing_next,
                status=status.HTTP_400_BAD_REQUEST,
                user=self.user,
            )

    def test_view_blocks_bad_redirect_target(self):
        with self.subTest("get"):
            self.app.get(
                self.subject_url_not_allowed_next,
                status=status.HTTP_400_BAD_REQUEST,
                user=self.user,
            )
        with self.subTest("post"):
            self.app.post(
                self.subject_url_not_allowed_next,
                status=status.HTTP_400_BAD_REQUEST,
                user=self.user,
            )

    def test_form_validates_input(self):
        with self.subTest("invalid empty form"):
            response = self.app.get(self.subject_url, status=200, user=self.user)
            form = response.forms["registrator-subject"]
            response = form.submit(status=200)
            self.assertContains(response, _("Use either BSN or KvK"), html=True)

        with self.subTest("invalid bsn"):
            response = self.app.get(self.subject_url, status=200, user=self.user)
            form = response.forms["registrator-subject"]
            form["bsn"] = "123"
            response = form.submit(status=200)
            message = _("BSN should have %(size)i characters.") % {
                "size": 9,
            }
            self.assertContains(response, message, html=True)

        with self.subTest("invalid kvk"):
            response = self.app.get(self.subject_url, status=200, user=self.user)
            form = response.forms["registrator-subject"]
            form["kvk"] = "123"
            response = form.submit(status=200)
            message = _("%(type)s should have %(size)i characters.") % {
                "type": _("KvK number"),
                "size": 8,
            }
            self.assertContains(response, message, html=True)

        with self.subTest("kvk branch number without kvk"):
            response = self.app.get(self.subject_url, status=200, user=self.user)
            form = response.forms["registrator-subject"]
            form["bsn"] = "115736499"
            form["kvk_branch_number"] = "000038509490"
            response = form.submit(status=200)
            self.assertContains(
                response,
                _("Branch number is only applicable for KvK values"),
                html=True,
            )
        with self.subTest("invalid with both bsn and kvk"):
            response = self.app.get(self.subject_url, status=200, user=self.user)
            form = response.forms["registrator-subject"]
            form["bsn"] = "115736499"
            form["kvk"] = "12345678"
            response = form.submit(status=200)
            self.assertContains(response, _("Use either BSN or KvK"), html=True)

        with self.subTest("valid bsn"):
            response = self.app.get(self.subject_url, status=200, user=self.user)
            form = response.forms["registrator-subject"]
            form["bsn"] = "115736499"
            response = form.submit(status=302)
            self.assertRedirects(response, self.form_url, fetch_redirect_response=False)

        with self.subTest("valid kvk"):
            response = self.app.get(self.subject_url, status=200, user=self.user)
            form = response.forms["registrator-subject"]
            form["kvk"] = "12345678"
            response = form.submit(status=302)
            self.assertRedirects(response, self.form_url, fetch_redirect_response=False)

        with self.subTest("valid kvk with branch number"):
            response = self.app.get(self.subject_url, status=200, user=self.user)
            form = response.forms["registrator-subject"]
            form["kvk"] = "12345678"
            form["kvk_branch_number"] = "000038509490"
            response = form.submit(status=302)
            self.assertRedirects(response, self.form_url, fetch_redirect_response=False)

        with self.subTest("valid click skip_subject"):
            response = self.app.get(self.subject_url, status=200, user=self.user)
            form = response.forms["registrator-subject"]
            response = form.submit("skip_subject", status=302)
            self.assertRedirects(response, self.form_url, fetch_redirect_response=False)

    def test_view_sets_registrator_subject_session_data(self):
        with self.subTest("bsn"):
            response = self.app.get(self.subject_url, status=200, user=self.user)
            form = response.forms["registrator-subject"]
            form["bsn"] = "115736499"
            response = form.submit(status=302)
            self.assertRedirects(response, self.form_url, fetch_redirect_response=False)

            self.assertIn(REGISTRATOR_SUBJECT_SESSION_KEY, self.app.session)
            data = self.app.session[REGISTRATOR_SUBJECT_SESSION_KEY]
            self.assertEqual(
                data, {"attribute": AuthAttribute.bsn, "value": "115736499"}
            )

        with self.subTest("kvk"):
            response = self.app.get(self.subject_url, status=200, user=self.user)
            form = response.forms["registrator-subject"]
            form["kvk"] = "12345678"
            response = form.submit(status=302)
            self.assertRedirects(response, self.form_url, fetch_redirect_response=False)

            self.assertIn(REGISTRATOR_SUBJECT_SESSION_KEY, self.app.session)
            data = self.app.session[REGISTRATOR_SUBJECT_SESSION_KEY]
            self.assertEqual(
                data,
                {
                    "attribute": AuthAttribute.kvk,
                    "value": "12345678",
                },
            )

        with self.subTest("kvk with branch number"):
            response = self.app.get(self.subject_url, status=200, user=self.user)
            form = response.forms["registrator-subject"]
            form["kvk"] = "12345678"
            form["kvk_branch_number"] = "000038509490"
            response = form.submit(status=302)
            self.assertRedirects(response, self.form_url, fetch_redirect_response=False)

            self.assertIn(REGISTRATOR_SUBJECT_SESSION_KEY, self.app.session)
            data = self.app.session[REGISTRATOR_SUBJECT_SESSION_KEY]
            self.assertEqual(
                data,
                {
                    "attribute": AuthAttribute.kvk,
                    "value": "12345678",
                    "branch_number": "000038509490",
                },
            )

        with self.subTest("skip_subject"):
            response = self.app.get(self.subject_url, status=200, user=self.user)
            form = response.forms["registrator-subject"]
            response = form.submit("skip_subject", status=302)
            self.assertRedirects(response, self.form_url, fetch_redirect_response=False)

            self.assertIn(REGISTRATOR_SUBJECT_SESSION_KEY, self.app.session)
            data = self.app.session[REGISTRATOR_SUBJECT_SESSION_KEY]
            self.assertEqual(data, {"skipped_subject_info": True})


class LogoutTestViewTests(TestCase):
    def test_no_auth_info_in_session(self):
        logout_url = reverse("authentication:logout")

        response = self.client.post(logout_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logout_calls_plugin_logout(self):
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session[REGISTRATOR_SUBJECT_SESSION_KEY] = {
            "attribute": AuthAttribute.bsn,
            "value": "123456782",
        }
        session.save()

        with patch(
            "openforms.authentication.contrib.digid.plugin.DigidAuthentication.logout"
        ) as m_logout:
            response = self.client.post(reverse("authentication:logout"), data={})

        m_logout.assert_called_once()

        self.assertRedirects(
            response,
            reverse("authentication:logout-confirmation"),
            fetch_redirect_response=False,
        )
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.client.session)
        self.assertNotIn(REGISTRATOR_SUBJECT_SESSION_KEY, self.client.session)
