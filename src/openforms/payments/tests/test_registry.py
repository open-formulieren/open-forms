from urllib.parse import quote

from django.http import HttpResponseRedirect
from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from rest_framework.reverse import reverse

from ...forms.tests.factories import FormStepFactory
from ...plugins.constants import UNIQUE_ID_MAX_LENGTH
from ..base import BasePlugin, PaymentInfo
from ..registry import Registry
from ..views import PaymentReturnView, PaymentStartView, PaymentWebhookView
from .factories import SubmissionPaymentFactory


class Plugin(BasePlugin):
    verbose_name = "some human readable label"
    return_method = "GET"
    webhook_method = "POST"

    def start_payment(self, request, payment):
        return PaymentInfo(type="get", url="http://testserver/foo")

    def handle_return(self, request, payment):
        return HttpResponseRedirect(payment.form_url)

    def handle_webhook(self, request):
        return None


class FailingPlugin(BasePlugin):
    verbose_name = "some human readable label"

    def start_payment(self, request, payment):
        raise Exception("start")

    def handle_return(self, request, payment):
        raise Exception("return")

    def handle_webhook(self, request):
        raise Exception("webhook")


class RegistryTests(TestCase):
    maxDiff = 1024

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

    def test_long_identifier(self):
        register = Registry()
        long_identifier = "x" * (UNIQUE_ID_MAX_LENGTH + 1)

        with self.assertRaisesMessage(
            ValueError,
            f"The unique identifier '{long_identifier}' is longer then {UNIQUE_ID_MAX_LENGTH} characters.",
        ):
            register(long_identifier)(Plugin)

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

        payment = SubmissionPaymentFactory.for_backend("plugin1")
        submission = payment.submission

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
        url = plugin.get_return_url(request, payment)
        self.assertRegex(url, r"^http://")
        self.assertEqual(
            url,
            reverse(
                "payments:return",
                request=request,
                kwargs={"uuid": payment.uuid},
            ),
        )
        # check the webhook url
        url = plugin.get_webhook_url(request)
        self.assertRegex(url, r"^http://")
        self.assertEqual(
            url,
            reverse(
                "payments:webhook",
                request=request,
                kwargs={"plugin_id": "plugin1"},
            ),
        )

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://foo.bar"]
    )
    def test_views(self):
        register = Registry()
        register("plugin1")(Plugin)
        plugin = register["plugin1"]

        payment = SubmissionPaymentFactory.for_backend(
            "plugin1", form_url="http://foo.bar"
        )
        submission = payment.submission

        # we need an arbitrary request
        factory = RequestFactory()
        init_request = factory.get("/foo")

        next_url_enc = quote("http://foo.bar")
        bad_url_enc = quote("http://buzz.bazz")

        # check the start view
        url = plugin.get_start_url(init_request, payment)

        start_view = PaymentStartView.as_view(register=register)

        with self.subTest("start ok"):
            request = factory.post(f"{url}?next={next_url_enc}")
            response = start_view(
                request, uuid=submission.uuid, plugin_id=plugin.identifier
            )
            self.assertEqual(
                response.data,
                {
                    "url": "http://testserver/foo",
                    "type": "get",
                    "data": None,
                },
            )
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
        url = plugin.get_return_url(request, payment)

        return_view = PaymentReturnView.as_view(register=register)

        with self.subTest("return ok"):
            request = factory.get(url)
            response = return_view(request, uuid=payment.uuid)
            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 302)

        with self.subTest("return bad method"):
            request = factory.post(url)
            response = return_view(request, uuid=payment.uuid)
            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "GET")

        with self.subTest("return bad plugin"):
            request = factory.get(url)
            payment_bad = SubmissionPaymentFactory.for_backend(
                "bad_plugin", form_url="http://foo.bar"
            )

            response = return_view(request, uuid=payment_bad.uuid)
            self.assertEqual(response.content, b"unknown plugin")
            self.assertEqual(response.status_code, 400)

        with self.subTest("return bad redirect"):
            request = factory.get(url)
            payment_bad = SubmissionPaymentFactory.for_backend(
                "plugin1", form_url="http://buzz.bazz"
            )

            response = return_view(request, uuid=payment_bad.uuid)
            self.assertEqual(response.content, b"redirect not allowed")
            self.assertEqual(response.status_code, 400)

        # check the webhook view
        url = plugin.get_webhook_url(request)

        webhook_view = PaymentWebhookView.as_view(register=register)

        with self.subTest("webhook ok"):
            request = factory.post(url)
            response = webhook_view(request, plugin_id=plugin.identifier)
            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 200)

        with self.subTest("webhook bad method"):
            request = factory.get(url)
            response = webhook_view(request, plugin_id=plugin.identifier)
            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "POST")

        with self.subTest("webhook bad plugin"):
            request = factory.get(url)
            response = webhook_view(request, plugin_id="bad_plugin")
            self.assertEqual(response.content, b"unknown plugin")
            self.assertEqual(response.status_code, 400)
