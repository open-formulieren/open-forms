from urllib.parse import quote

from django.http import HttpResponse, HttpResponseRedirect
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from rest_framework.reverse import reverse

from ..base import BasePlugin
from ..registry import Registry
from ..views import (
    PaymentReturnView,
    PaymentStartView,
)
from ...forms.tests.factories import FormStepFactory
from ...submissions.tests.factories import SubmissionFactory


class Plugin(BasePlugin):
    verbose_name = "some human readable label"

    def start_payment(self, request, submission, form_url, amount):
        return HttpResponse("start")

    def handle_return(self, request, submission):
        return HttpResponseRedirect(request.GET.get("next"))


class FailingPlugin(BasePlugin):
    verbose_name = "some human readable label"

    def start_payment(self, request, submission, form_url, amount):
        raise Exception("start")

    def handle_return(self, request, submission):
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
            form__payment_backend="plugin1",
            form__payment_backend_options={"foo": 1},
        )
        form = step.form
        self.assertEqual(form.payment_backend, "plugin1")

        options = register.get_options(request, form)
        self.assertEqual(len(options), 1)

        option = options[0]
        self.assertEqual(option.identifier, "plugin1")
        self.assertEqual(option.label, "some human readable label")

    def test_urls(self):
        register = Registry()
        register("plugin1")(Plugin)
        plugin = register["plugin1"]

        submission = SubmissionFactory(
            form__slug="myform",
            form__payment_backend="plugin1",
        )

        # we need an arbitrary request
        factory = RequestFactory()
        request = factory.get("/foo")

        # check the start url
        url = plugin.get_start_url(request, submission)
        self.assertRegex(url, r"^http://")
        self.assertEqual(
            url,
            reverse(
                "payments:start",
                request=request,
                kwargs={"uuid": submission.uuid, "plugin_id": "plugin1"},
            ),
        )

        # check the return url
        url = plugin.get_return_url(request, submission)
        self.assertRegex(url, r"^http://")
        self.assertEqual(
            url,
            reverse(
                "payments:return",
                request=request,
                kwargs={"uuid": submission.uuid, "plugin_id": "plugin1"},
            ),
        )

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://foo.bar"]
    )
    def test_views(self):
        register = Registry()
        register("plugin1")(Plugin)
        plugin = register["plugin1"]

        submission = SubmissionFactory(
            form__slug="myform",
            form__payment_backend="plugin1",
        )

        # we need an arbitrary request
        factory = RequestFactory()
        init_request = factory.get("/foo")

        next_url_enc = quote("http://foo.bar")
        bad_url_enc = quote("http://buzz.bazz")

        # check the start view
        url = plugin.get_start_url(init_request, submission)

        start_view = PaymentStartView.as_view(register=register)

        with self.subTest("start ok"):
            request = factory.post(f"{url}?next={next_url_enc}")
            response = start_view(
                request, uuid=submission.uuid, plugin_id=plugin.identifier
            )
            self.assertEqual(response.content, b"start")
            self.assertEqual(response.status_code, 200)

        with self.subTest("start missing next"):
            request = factory.post(url)
            response = start_view(
                request, uuid=submission.uuid, plugin_id=plugin.identifier
            )
            self.assertEqual(response.content, b"missing 'next' parameter")
            self.assertEqual(response.status_code, 400)

        with self.subTest("start bad plugin"):
            request = factory.post(f"{url}?next={next_url_enc}")
            response = start_view(request, uuid=submission.uuid, plugin_id="bad_plugin")
            self.assertEqual(response.content, b"unknown plugin")
            self.assertEqual(response.status_code, 400)

        with self.subTest("start bad redirect"):
            request = factory.post(f"{url}?next={bad_url_enc}")
            response = start_view(
                request, uuid=submission.uuid, plugin_id=plugin.identifier
            )
            self.assertEqual(response.content, b"redirect not allowed")
            self.assertEqual(response.status_code, 400)

        # check the return view
        url = plugin.get_return_url(request, submission)

        return_view = PaymentReturnView.as_view(register=register)

        with self.subTest("return ok"):
            request = factory.get(f"{url}?next={next_url_enc}")
            response = return_view(
                request, uuid=submission.uuid, plugin_id=plugin.identifier
            )
            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 302)

        with self.subTest("return bad method"):
            request = factory.post(f"{url}?next={next_url_enc}")
            response = return_view(
                request, uuid=submission.uuid, plugin_id=plugin.identifier
            )
            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "GET")

        with self.subTest("return bad plugin"):
            request = factory.get(f"{url}?next={next_url_enc}")
            response = return_view(
                request, uuid=submission.uuid, plugin_id="bad_plugin"
            )
            self.assertEqual(response.content, b"unknown plugin")
            self.assertEqual(response.status_code, 400)

        with self.subTest("return bad redirect"):
            request = factory.get(f"{url}?next={bad_url_enc}")
            response = return_view(
                request, uuid=submission.uuid, plugin_id=plugin.identifier
            )
            self.assertEqual(response.content, b"redirect not allowed")
            self.assertEqual(response.status_code, 400)
