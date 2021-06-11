from urllib.parse import quote

from django.http import HttpResponse, HttpResponseRedirect
from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from rest_framework.reverse import reverse

from ...forms.tests.factories import FormStepFactory
from ..base import BasePlugin
from ..registry import Registry
from ..views import (
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
        # override and restore the plugin registry used by the views
        def restore_views(*args):
            AuthenticationStartView.register, AuthenticationReturnView.register = args

        self.addCleanup(
            restore_views,
            AuthenticationStartView.register,
            AuthenticationReturnView.register,
        )

        register = Registry()
        AuthenticationStartView.register = register
        AuthenticationReturnView.register = register

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

        next_url_enc = quote("http://foo.bar")
        bad_url_enc = quote("http://buzz.bazz")

        # check the start view
        url = plugin.get_start_url(request, form)

        with self.subTest("start ok"):
            response = self.client.get(f"{url}?next={next_url_enc}")
            self.assertEqual(response.content, b"start")
            self.assertEqual(response.status_code, 200)

        with self.subTest("start missing next"):
            response = self.client.get(url)
            self.assertEqual(response.content, b"missing 'next' parameter")
            self.assertEqual(response.status_code, 400)

        with self.subTest("start missing bad plugin"):
            response = self.client.get(
                f"{url}?next={next_url_enc}".replace("plugin1", "bad_plugin")
            )
            self.assertEqual(response.content, b"unknown plugin")
            self.assertEqual(response.status_code, 400)

        with self.subTest("start bad redirect"):
            response = self.client.get(f"{url}?next={bad_url_enc}")
            self.assertEqual(response.content, b"redirect not allowed")
            self.assertEqual(response.status_code, 400)

        # check the return view
        url = plugin.get_return_url(request, form)

        with self.subTest("return ok"):
            response = self.client.get(f"{url}?next={next_url_enc}")
            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 302)

        with self.subTest("return bad method"):
            response = self.client.post(f"{url}?next={next_url_enc}")
            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "GET")

        with self.subTest("return missing bad plugin"):
            response = self.client.get(
                f"{url}?next={next_url_enc}".replace("plugin1", "bad_plugin")
            )
            self.assertEqual(response.content, b"unknown plugin")
            self.assertEqual(response.status_code, 400)

        with self.subTest("return bad redirect"):
            response = self.client.get(f"{url}?next={bad_url_enc}")
            self.assertEqual(response.content, b"redirect not allowed")
            self.assertEqual(response.status_code, 400)

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
