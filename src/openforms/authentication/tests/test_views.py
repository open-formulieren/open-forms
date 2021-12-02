from urllib.parse import quote

from django.test import override_settings
from django.test.client import RequestFactory

from furl import furl
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import FormStepFactory

from ..registry import Registry
from ..views import (
    BACKEND_OUTAGE_RESPONSE_PARAMETER,
    AuthenticationReturnView,
    AuthenticationStartView,
)
from .mocks import FailingPlugin, Plugin


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

        next_url_enc = quote("http://foo.bar")
        bad_url_enc = quote("http://buzz.bazz")

        # check the start view
        url = plugin.get_start_url(init_request, form)

        start_view = AuthenticationStartView.as_view(register=register)

        with self.subTest("start ok"):
            request = factory.get(f"{url}?next={next_url_enc}")
            response = start_view(request, slug=form.slug, plugin_id=plugin.identifier)
            self.assertEqual(response.content, b"start")
            self.assertEqual(response.status_code, 200)

        with self.subTest("start missing next"):
            request = factory.get(url)
            response = start_view(request, slug=form.slug, plugin_id=plugin.identifier)
            self.assertEqual(response.content, b"missing 'next' parameter")
            self.assertEqual(response.status_code, 400)

        with self.subTest("start bad plugin"):
            request = factory.get(f"{url}?next={next_url_enc}")
            response = start_view(request, slug=form.slug, plugin_id="bad_plugin")
            self.assertEqual(response.content, b"unknown plugin")
            self.assertEqual(response.status_code, 400)

        with self.subTest("start bad redirect"):
            request = factory.get(f"{url}?next={bad_url_enc}")
            response = start_view(request, slug=form.slug, plugin_id=plugin.identifier)
            self.assertEqual(response.content, b"redirect not allowed")
            self.assertEqual(response.status_code, 400)

        # check the return view
        url = plugin.get_return_url(request, form)

        return_view = AuthenticationReturnView.as_view(register=register)

        with self.subTest("return ok"):
            request = factory.get(f"{url}?next={next_url_enc}")
            response = return_view(request, slug=form.slug, plugin_id=plugin.identifier)
            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 302)

        with self.subTest("return bad method"):
            request = factory.post(f"{url}?next={next_url_enc}")
            response = return_view(request, slug=form.slug, plugin_id=plugin.identifier)
            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "GET")

        with self.subTest("return bad plugin"):
            request = factory.get(f"{url}?next={next_url_enc}")
            response = return_view(request, slug=form.slug, plugin_id="bad_plugin")
            self.assertEqual(response.content, b"unknown plugin")
            self.assertEqual(response.status_code, 400)

        with self.subTest("return bad redirect"):
            request = factory.get(f"{url}?next={bad_url_enc}")
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
        next_url_enc = quote("http://foo.bar?bazz=buzz")

        url = plugin.get_start_url(init_request, form)

        start_view = AuthenticationStartView.as_view(register=register)
        response = start_view(
            factory.get(f"{url}?next={next_url_enc}"),
            slug=form.slug,
            plugin_id="plugin1",
        )

        expected = furl("http://foo.bar?bazz=buzz")
        expected.args[BACKEND_OUTAGE_RESPONSE_PARAMETER] = "plugin1"
        self.assertEqual(furl(response["Location"]), expected)
