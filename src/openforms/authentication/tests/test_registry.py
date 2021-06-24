from urllib.parse import quote

from django.http import HttpResponse, HttpResponseRedirect
from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from furl import furl
from rest_framework.reverse import reverse

from ...forms.tests.factories import FormStepFactory
from ..base import BasePlugin
from ..registry import Registry
from ..views import (
    BACKEND_OUTAGE_RESPONSE_PARAMETER,
    AuthenticationReturnView,
    AuthenticationStartView,
    allow_redirect_url,
)


class Plugin(BasePlugin):
    verbose_name = "some human readable label"

    def start_login(self, request, form, form_url):
        return HttpResponse("start")

    def handle_return(self, request, form):
        return HttpResponseRedirect(request.GET.get("next"))


class FailingPlugin(BasePlugin):
    verbose_name = "some human readable label"

    def start_login(self, request, form, form_url):
        raise Exception("start")

    def handle_return(self, request, form):
        raise Exception("return")


class RegistryTests(TestCase):
    def test_register_function(self):
        register = Registry()

        register("plugin1")(Plugin)

        plugin = register["plugin1"]

        self.assertIsInstance(plugin, Plugin)
        self.assertEqual(plugin.identifier, "plugin1")
        self.assertEqual(plugin.verbose_name, "some human readable label")
        self.assertEqual(plugin.get_label(), plugin.verbose_name)

    def test_duplicate_identifier(self):
        register = Registry()
        register("plugin")(Plugin)

        with self.assertRaisesMessage(
            ValueError,
            "The unique identifier 'plugin' is already present in the registry",
        ):
            register("plugin")(Plugin)

    def test_get_choices(self):
        register = Registry()
        register("plugin1")(Plugin)

        choices = register.get_choices()
        self.assertEqual(choices, [("plugin1", "some human readable label")])

    def test_get_options(self):
        register = Registry()
        register("plugin1")(Plugin)
        plugin = register["plugin1"]

        factory = RequestFactory()
        request = factory.get("/xyz")
        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["plugin1"],
            form_definition__login_required=True,
        )
        form = step.form
        self.assertEqual(form.authentication_backends, ["plugin1"])

        options = register.get_options(request, form)
        self.assertEqual(len(options), 1)

        option = options[0]
        self.assertEqual(option.identifier, "plugin1")
        self.assertEqual(option.label, "some human readable label")
        self.assertEqual(option.url, plugin.get_start_url(request, form))

    def test_urls(self):
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
        request = factory.get("/foo")

        # check the start url
        url = plugin.get_start_url(request, form)
        self.assertRegex(url, r"^http://")
        self.assertEqual(
            url,
            reverse(
                "authentication:start",
                request=request,
                kwargs={"slug": "myform", "plugin_id": "plugin1"},
            ),
        )

        # check the return url
        url = plugin.get_return_url(request, form)
        self.assertRegex(url, r"^http://")
        self.assertEqual(
            url,
            reverse(
                "authentication:return",
                request=request,
                kwargs={"slug": "myform", "plugin_id": "plugin1"},
            ),
        )

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://foo.bar"]
    )
    def test_views(self):
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

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False,
        CORS_ALLOWED_ORIGINS=[],
        CORS_ALLOWED_ORIGIN_REGEXES=[],
    )
    def test_allow_redirect_url(self):
        self.assertEqual(allow_redirect_url("http://foo.bar"), False)
        self.assertEqual(allow_redirect_url("http://foo.bar/bazz"), False)
        self.assertEqual(allow_redirect_url("https://foo.bar"), False)
        self.assertEqual(allow_redirect_url("http://bazz.buzz"), False)

        with self.settings(
            CORS_ALLOW_ALL_ORIGINS=True,
        ):
            self.assertEqual(allow_redirect_url("http://foo.bar"), True)
            self.assertEqual(allow_redirect_url("http://foo.bar/bazz"), True)
            self.assertEqual(allow_redirect_url("https://foo.bar"), True)
            self.assertEqual(allow_redirect_url("http://bazz.buzz"), True)

        with self.settings(
            CORS_ALLOWED_ORIGINS=["http://foo.bar"],
        ):
            self.assertEqual(allow_redirect_url("http://foo.bar"), True)
            self.assertEqual(allow_redirect_url("http://foo.bar/bazz"), True)
            self.assertEqual(allow_redirect_url("https://foo.bar"), False)
            self.assertEqual(allow_redirect_url("http://bazz.buzz"), False)

        with self.settings(
            CORS_ALLOWED_ORIGIN_REGEXES=[r".*foo.*"],
        ):
            self.assertEqual(allow_redirect_url("http://foo.bar"), True)
            self.assertEqual(allow_redirect_url("http://foo.bar/bazz"), True)
            self.assertEqual(allow_redirect_url("https://foo.bar"), True)
            self.assertEqual(allow_redirect_url("http://bazz.buzz"), False)
